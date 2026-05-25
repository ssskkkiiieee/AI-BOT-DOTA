package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

func main() {
	replayPath := flag.String("file", "", "Path to the .dem replay file")
	flag.Parse()

	f, err := os.Open(*replayPath)
	if err != nil {
		fmt.Printf("Error opening file: %s\n", err)
		os.Exit(1)
	}
	defer f.Close()

	parser, err := manta.NewStreamParser(f)
	if err != nil {
		fmt.Printf("Error creating parser: %s\n", err)
		os.Exit(1)
	}

	found := false
	parser.Callbacks.OnCDemoPacket(func(msg *dota.CDemoPacket) error {
		if found {
			return nil
		}
		gr := parser.FilterEntity(func(e *manta.Entity) bool {
			return e.GetClassName() == "CDOTAGamerulesProxy"
		})
		if len(gr) > 0 {
			found = true
			fmt.Println("=== CDOTAGamerulesProxy found! ===")
			m := gr[0].Map()
			for k, v := range m {
				if v != nil {
					fmt.Printf("Key: %s | Value: %v | Type: %T\n", k, v, v)
				}
			}
			parser.Stop()
		}
		return nil
	})

	parser.Start()
}
