package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"runtime/debug"
	"sort"
	"strconv"
	"strings"

	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// Unit represents a simplified hero or creep in the game
type Unit struct {
	Index     int32
	ClassName string
	Name      string
	Team      int32
	X         float32
	Y         float32
	Health    int32
	MaxHealth int32
	Mana      int32
	MaxMana   int32
	Damage    int32
}

func main() {
	// CLI Flags
	replayPath := flag.String("file", "", "Path to the .dem replay file")
	flag.Parse()

	if *replayPath == "" {
		fmt.Println("Usage: go run parser.go -file <path_to_replay.dem>")
		os.Exit(1)
	}

	// Open the replay file
	f, err := os.Open(*replayPath)
	if err != nil {
		fmt.Printf("Error opening replay file: %s\n", err)
		os.Exit(1)
	}
	defer f.Close()

	// Create output CSV file path
	matchID := strings.TrimSuffix(filepath.Base(*replayPath), ".dem")
	csvPath := filepath.Join("C:\\бот\\data", matchID+".csv")
	csvFile, err := os.Create(csvPath)
	if err != nil {
		fmt.Printf("Error creating CSV file: %s\n", err)
		os.Exit(1)
	}
	defer csvFile.Close()

	writer := csv.NewWriter(csvFile)
	defer writer.Flush()

	// Write CSV Header
	header := []string{
		"tick", "game_time", 
		"hero_name", "hero_team", "hero_x", "hero_y", "hero_hp", "hero_max_hp", "hero_mana", "hero_max_mana",
	}
	// Up to 5 nearest creeps (padded if less)
	for i := 1; i <= 5; i++ {
		pfx := "creep_" + strconv.Itoa(i) + "_"
		header = append(header, []string{
			pfx + "id", pfx + "x", pfx + "y", pfx + "hp", pfx + "max_hp", pfx + "team", pfx + "dist",
		}...)
	}
	writer.Write(header)

	// Create Manta Parser
	parser, err := manta.NewStreamParser(f)
	if err != nil {
		fmt.Printf("Error creating parser: %s\n", err)
		os.Exit(1)
	}

	// State tracking
	units := make(map[int32]*Unit)
	var lastLoggedTick uint32 = 0
	var spawnedSnapshotCount int = 0

	// Open or create the shared wards file in append mode
	wardsFile, _ := os.OpenFile("C:\\бот\\data\\wards_raw.csv", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if wardsFile != nil {
		defer wardsFile.Close()
		fi, _ := wardsFile.Stat()
		if fi.Size() == 0 {
			wardsFile.WriteString("match_id,tick,game_time,class_name,team,x,y\n")
		}
	}

	// Handle entity updates
	parser.OnEntity(func(e *manta.Entity, op manta.EntityOp) (err error) {
		defer func() {
			if r := recover(); r != nil {
				fmt.Printf("Panic caught in OnEntity: %v\nStack trace:\n%s\n", r, debug.Stack())
				err = fmt.Errorf("panic: %v", r)
			}
		}()

		if e == nil {
			return nil
		}

		className := e.GetClassName()

		// If it's a ward entity, log its placement immediately!
		if className == "CDOTA_NPC_Observer_Ward" || className == "CDOTA_NPC_Sentry_Ward" {
			if op.Flag(manta.EntityOpCreated) {
				cellX, hasCellX := e.GetUint32("CBodyComponent.m_cellX")
				cellY, hasCellY := e.GetUint32("CBodyComponent.m_cellY")
				vecX, hasVecX := e.GetFloat32("CBodyComponent.m_vecX")
				vecY, hasVecY := e.GetFloat32("CBodyComponent.m_vecY")
				team, _ := e.GetInt32("m_iTeamNum")

				if hasCellX && hasCellY && hasVecX && hasVecY {
					posX := float32(cellX)*128.0 + vecX
					posY := float32(cellY)*128.0 + vecY
					gameTime := float32(parser.Tick) / 30.0
					logLine := fmt.Sprintf("%s,%d,%.2f,%s,%d,%.2f,%.2f\n", 
						matchID, parser.Tick, gameTime, className, team, posX, posY)
					
					if wardsFile != nil {
						wardsFile.WriteString(logLine)
					}
				}
			}
			return nil
		}

		isHero := strings.HasPrefix(className, "CDOTA_Unit_Hero_")
		isCreep := strings.HasPrefix(className, "CDOTA_BaseNPC_Creep_") || strings.HasPrefix(className, "CDOTA_BaseNPC_Fort")

		// If it's not a unit we care about, skip
		if !isHero && !isCreep {
			return nil
		}

		index := e.GetIndex()

		// Handle Deletions
		if op.Flag(manta.EntityOpDeleted) || op.Flag(manta.EntityOpLeft) {
			delete(units, index)
			return nil
		}

		// Read properties safely
		team, _ := e.GetInt32("m_iTeamNum")
		hp, _ := e.GetInt32("m_iHealth")
		maxHp, _ := e.GetInt32("m_iMaxHealth")
		
		// Parse coordinates using Source 2 CBodyComponent grid system
		cellX, hasCellX := e.GetUint32("CBodyComponent.m_cellX")
		cellY, hasCellY := e.GetUint32("CBodyComponent.m_cellY")
		vecX, hasVecX := e.GetFloat32("CBodyComponent.m_vecX")
		vecY, hasVecY := e.GetFloat32("CBodyComponent.m_vecY")

		var posX float32 = 0.0
		var posY float32 = 0.0
		if hasCellX && hasCellY && hasVecX && hasVecY {
			posX = float32(cellX)*128.0 + vecX
			posY = float32(cellY)*128.0 + vecY
		}

		mana, _ := e.GetInt32("m_flMana")
		maxMana, _ := e.GetInt32("m_flMaxMana")
		damage, _ := e.GetInt32("m_iDamageMin") // baseline attack damage

		// Find or create Unit
		unit, exists := units[index]
		if !exists {
			unit = &Unit{
				Index:     index,
				ClassName: className,
				Name:      className,
			}
			units[index] = unit
		}

		// Update fields
		unit.Team = team
		unit.X = posX
		unit.Y = posY
		unit.Health = hp
		unit.MaxHealth = maxHp
		unit.Mana = mana
		unit.MaxMana = maxMana
		unit.Damage = damage

		return nil
	})

	// Register callback to track game rules and snap updates
	parser.Callbacks.OnCDemoPacket(func(msg *dota.CDemoPacket) (err error) {
		defer func() {
			if r := recover(); r != nil {
				fmt.Printf("Panic caught in OnCDemoPacket: %v\nStack trace:\n%s\n", r, debug.Stack())
				err = fmt.Errorf("panic: %v", r)
			}
		}()

		// Periodically write snapshots (every 10 ticks, approx 333ms)
		if parser.Tick-lastLoggedTick >= 10 {
			lastLoggedTick = parser.Tick

			// Calculate game time directly from ticks (30 ticks per second)
			gameTime := float32(parser.Tick) / 30.0

			// Write snapshot and count active rows
			rowsWritten := writeSnapshot(parser.Tick, gameTime, units, writer)
			if rowsWritten > 0 {
				spawnedSnapshotCount++
			}

			// Exiting after writing 1800 snapshots (~10 minutes of active gameplay from spawn!)
			if spawnedSnapshotCount >= 1800 {
				parser.Stop()
			}
		}
		return nil
	})

	fmt.Println("Parsing replay...")
	err = parser.Start()
	if err != nil {
		fmt.Printf("Parser stopped with error: %s\n", err)
	}

	fmt.Printf("Parse complete! Data written to: %s\n", csvPath)
}

// Helper to write a state snapshot to CSV. Returns the number of logged rows.
func writeSnapshot(tick uint32, gameTime float32, units map[int32]*Unit, writer *csv.Writer) int {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("Panic caught in writeSnapshot: %v\nStack trace:\n%s\n", r, debug.Stack())
		}
	}()

	// Find all heroes
	var heroes []*Unit
	var creeps []*Unit

	for _, u := range units {
		if u == nil {
			continue
		}
		if strings.HasPrefix(u.ClassName, "CDOTA_Unit_Hero_") {
			// Only include heroes that have spawned and are on the map
			if u.X != 0.0 && u.Y != 0.0 {
				heroes = append(heroes, u)
			}
		} else {
			// Visible active creep
			if u.Health > 0 && u.X != 0.0 && u.Y != 0.0 {
				creeps = append(creeps, u)
			}
		}
	}

	rowsLogged := 0

	// For each hero, log their state and nearest creeps
	for _, hero := range heroes {
		if hero == nil {
			continue
		}
		// If hero is dead, skip
		if hero.Health <= 0 {
			continue
		}

		// Structure: tick, game_time, hero_name, hero_team, hero_x, hero_y, hero_hp, hero_max_hp, hero_mana, hero_max_mana
		row := []string{
			strconv.FormatUint(uint64(tick), 10),
			strconv.FormatFloat(float64(gameTime), 'f', 2, 32),
			hero.ClassName,
			strconv.Itoa(int(hero.Team)),
			strconv.FormatFloat(float64(hero.X), 'f', 2, 32),
			strconv.FormatFloat(float64(hero.Y), 'f', 2, 32),
			strconv.Itoa(int(hero.Health)),
			strconv.Itoa(int(hero.MaxHealth)),
			strconv.Itoa(int(hero.Mana)),
			strconv.Itoa(int(hero.MaxMana)),
		}

		// Calculate distance to all creeps and sort
		type CreepDist struct {
			Unit *Unit
			Dist float64
		}
		var creepDists []CreepDist

		for _, creep := range creeps {
			if creep == nil {
				continue
			}
			dx := float64(creep.X - hero.X)
			dy := float64(creep.Y - hero.Y)
			dist := math.Sqrt(dx*dx + dy*dy)
			
			// Only track creeps in typical laning range (1500 units)
			if dist < 1500.0 {
				creepDists = append(creepDists, CreepDist{Unit: creep, Dist: dist})
			}
		}

		// Sort by distance ascending
		sort.Slice(creepDists, func(i, j int) bool {
			return creepDists[i].Dist < creepDists[j].Dist
		})

		// Append up to 5 nearest creeps
		for i := 0; i < 5; i++ {
			if i < len(creepDists) && creepDists[i].Unit != nil {
				c := creepDists[i].Unit
				d := creepDists[i].Dist
				row = append(row, []string{
					strconv.Itoa(int(c.Index)),
					strconv.FormatFloat(float64(c.X), 'f', 2, 32),
					strconv.FormatFloat(float64(c.Y), 'f', 2, 32),
					strconv.Itoa(int(c.Health)),
					strconv.Itoa(int(c.MaxHealth)),
					strconv.Itoa(int(c.Team)),
					strconv.FormatFloat(d, 'f', 2, 32),
				}...)
			} else {
				// Pad with zeros if less than 5 creeps
				row = append(row, []string{"0", "0.0", "0.0", "0", "0", "0", "0.0"}...)
			}
		}

		// Write to CSV
		writer.Write(row)
		rowsLogged++
	}

	return rowsLogged
}
