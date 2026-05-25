import os
import requests
import json
import time

API_KEY = "deb3dc65-2e3a-4c9e-9d16-bce6ff480468"
DOTA_VSCRIPTS_BOTS_DIR = r"C:\stea\steamapps\common\dota 2 beta\game\dota\scripts\vscripts\bots"

def get_heroes():
    print("[API] Fetching hero list from OpenDota...")
    url = f"https://api.opendota.com/api/heroes?api_key={API_KEY}"
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Fetching heroes failed: {e}")
        return []

def get_hero_abilities_mapping():
    print("[API] Fetching hero abilities mapping from dotaconstants...")
    url = "https://raw.githubusercontent.com/odota/dotaconstants/master/build/hero_abilities.json"
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Fetching hero abilities failed: {e}")
        return {}

def clean_ability_name(a):
    if isinstance(a, str):
        return a
    elif isinstance(a, dict):
        return a.get('name', '')
    elif isinstance(a, list):
        if len(a) > 0:
            return clean_ability_name(a[0])
    return str(a)

def main():
    print("=== Dota 2 127-Hero Pro Skill Casting Script Generator ===")
    
    heroes = get_heroes()
    abilities_map = get_hero_abilities_mapping()
    
    if not heroes or not abilities_map:
        print("Error: Could not retrieve data from APIs. Aborting.")
        return
        
    os.makedirs(DOTA_VSCRIPTS_BOTS_DIR, exist_ok=True)
    
    generated_count = 0
    
    for hero in heroes:
        hero_full_name = hero['name']  # npc_dota_hero_lina
        hero_short_name = hero_full_name.replace("npc_dota_hero_", "") # lina
        
        # Get abilities and talents
        abilities_info = abilities_map.get(hero_full_name, {})
        raw_abils = abilities_info.get('abilities', [])
        basic_abils = []
        for a in raw_abils:
            name = clean_ability_name(a)
            if name and not name.startswith('generic_hidden') and name != 'attribute_bonus':
                basic_abils.append(name)
                
        raw_talents = abilities_info.get('talents', [])
        talents = []
        for t in raw_talents:
            name = clean_ability_name(t)
            if name:
                talents.append(name)
                
        real_basics = []
        ultimate = None
        
        for abil in basic_abils:
            if "ultimate" in abil or abil in [
                "antimage_mana_void", "axe_culling_blade", "bane_fiends_grip", "bloodseeker_rupture", 
                "crystal_maiden_freezing_field", "juggernaut_omnislash", "lina_laguna_blade", 
                "lion_finger_of_death", "pudge_dismember", "queenofpain_sonic_wave", 
                "shadow_shaman_mass_serpent_ward", "nevermore_requiem", "phantom_assassin_coup_de_grace",
                "zuus_thundergods_wrath", "warlock_rain_of_chaos", "faceless_void_chronosphere",
                "tidehunter_ravage", "enigma_black_hole", "earthshaker_echo_slam", "sven_gods_strength"
            ]:
                ultimate = abil
            elif len(real_basics) < 3:
                real_basics.append(abil)
                
        if not ultimate and len(basic_abils) > 3:
            ultimate = basic_abils[3]
        elif not ultimate and len(basic_abils) > 0:
            ultimate = basic_abils[-1]
            
        while len(real_basics) < 3:
            real_basics.append("generic_hidden")
            
        if not ultimate:
            ultimate = "generic_hidden"
            
        t10 = talents[0] if len(talents) > 0 else "special_bonus_attributes"
        t15 = talents[2] if len(talents) > 2 else "special_bonus_attributes"
        t20 = talents[4] if len(talents) > 4 else "special_bonus_attributes"
        t25 = talents[6] if len(talents) > 6 else "special_bonus_attributes"
        
        # Build Standard leveling list
        std_build = []
        for level in range(1, 31):
            if level in [6, 12, 18]:
                std_build.append(ultimate)
            elif level == 10:
                std_build.append(t10)
            elif level == 15:
                std_build.append(t15)
            elif level == 20:
                std_build.append(t20)
            elif level == 25:
                std_build.append(t25)
            elif level in [1, 3, 5, 7]:
                std_build.append(real_basics[0])
            elif level in [2, 8, 9, 11]:
                std_build.append(real_basics[1])
            elif level in [4, 13, 14, 16]:
                std_build.append(real_basics[2])
            else:
                std_build.append("special_bonus_attributes")
                
        # Generate the Lua File content
        lua_content = f"""-- ============================================================================
-- ability_item_usage_{hero_short_name}.lua
-- Dedicated pro-tier casting logic for {hero_full_name}
-- Automatically generated by Antigravity Code Generator
-- ============================================================================

local SUPPORT_HEROES = {{
    ["npc_dota_hero_crystal_maiden"] = true, ["npc_dota_hero_lion"] = true,
    ["npc_dota_hero_witch_doctor"] = true, ["npc_dota_hero_dazzle"] = true,
    ["npc_dota_hero_shadow_shaman"] = true, ["npc_dota_hero_lich"] = true,
    ["npc_dota_hero_oracle"] = true, ["npc_dota_hero_disruptor"] = true,
    ["npc_dota_hero_keeper_of_the_light"] = true, ["npc_dota_hero_bane"] = true,
    ["npc_dota_hero_warlock"] = true, ["npc_dota_hero_ancient_apparition"] = true,
    ["npc_dota_hero_grimstroke"] = true, ["npc_dota_hero_jakiro"] = true,
    ["npc_dota_hero_skywrath_mage"] = true, ["npc_dota_hero_treant"] = true,
    ["npc_dota_hero_undying"] = true, ["npc_dota_hero_rubick"] = true,
    ["npc_dota_hero_chen"] = true, ["npc_dota_hero_wisp"] = true,
    ["npc_dota_hero_shadow_demon"] = true, ["npc_dota_hero_snapfire"] = true,
    ["npc_dota_hero_mirana"] = true, ["npc_dota_hero_bounty_hunter"] = true,
    ["npc_dota_hero_nyx_assassin"] = true, ["npc_dota_hero_spirit_breaker"] = true,
    ["npc_dota_hero_earth_spirit"] = true, ["npc_dota_hero_tusk"] = true,
    ["npc_dota_hero_elder_titan"] = true, ["npc_dota_hero_techies"] = true,
    ["npc_dota_hero_hoodwink"] = true
}}

local ABILITY_BUILD = {{
"""
        for abil in std_build:
            lua_content += f'    "{abil}",\n'
        lua_content += f"""}}

function AbilityLevelUpThink()
    local bot = GetBot()
    if bot == nil or bot:GetAbilityPoints() <= 0 then return end
    
    local level = bot:GetLevel()
    local ability_name = ABILITY_BUILD[level]
    
    if ability_name ~= nil and ability_name ~= "special_bonus_attributes" and ability_name ~= "generic_hidden" then
        local abil = bot:GetAbilityByName(ability_name)
        if abil ~= nil and abil:CanAbilityBeUpgraded() then
            bot:ActionImmediate_LevelAbility(ability_name)
            return
        end
    end
    
    -- Level stats fallback
    local stats = bot:GetAbilityByName("special_bonus_attributes")
    if stats and stats:CanAbilityBeUpgraded() then
        bot:ActionImmediate_LevelAbility("special_bonus_attributes")
    end
end

-- Distance calculator 2D
local function GetDistance(v1, v2)
    if v1 == nil or v2 == nil then return 999999 end
    return math.sqrt((v1.x - v2.x)^2 + (v1.y - v2.y)^2)
end

-- 1. TARGET VULNERABILITY SCORING SYSTEM (Умный выбор целей)
local function GetBestTarget(bot, range)
    local enemies = bot:GetNearbyHeroes(range, true, BOT_MODE_NONE)
    if enemies == nil or #enemies == 0 then return nil end
    
    local best_target = nil
    local max_score = -99999
    
    for _, enemy in ipairs(enemies) do
        if enemy ~= nil and enemy:IsAlive() and not enemy:IsInvulnerable() then
            local score = 0
            local hp_pct = enemy:GetHealth() / enemy:GetMaxHealth()
            
            -- High priority to kill low health targets (Kill Secure)
            score = score + (1.0 - hp_pct) * 100
            
            -- Absolute priority to interrupt channeling enemies (TP, Black Hole, etc.)
            if enemy:IsChanneling() then
                score = score + 500
            end
            
            -- Priority to Core heroes in teamfights
            local name = enemy:GetUnitName()
            if not SUPPORT_HEROES[name] then
                score = score + 40
            end
            
            -- Prevent stun overlap (don't nuke/stun already locked down targets unless to secure kill)
            if enemy:HasModifier("modifier_stunned") or enemy:HasModifier("modifier_hexed") then
                score = score - 30
            end
            
            if score > max_score then
                max_score = score
                best_target = enemy
            end
        end
    end
    
    return best_target
end

-- 2. ACTIVE OFFENSIVE ITEM CHAINING SYSTEM (Цепочка прокаста предметов)
local function UseOffensiveItems(bot, target)
    if target == nil then return false end
    local dist = GetDistance(bot:GetLocation(), target:GetLocation())
    
    -- 1. Hex (Guinsoo)
    local hex = bot:FindItemSlot("item_sheepstick")
    if hex ~= nil and hex >= 0 and hex <= 5 and dist <= 800 then
        local item = bot:GetItemInSlot(hex)
        if item and item:IsFullyCastable() then
            bot:Action_UseAbilityOnEntity(item, target)
            return true
        end
    end
    
    -- 2. Orchid / Bloodthorn
    local orchid = bot:FindItemSlot("item_orchid") or bot:FindItemSlot("item_bloodthorn")
    if orchid ~= nil and orchid >= 0 and orchid <= 5 and dist <= 900 then
        local item = bot:GetItemInSlot(orchid)
        if item and item:IsFullyCastable() then
            bot:Action_UseAbilityOnEntity(item, target)
            return true
        end
    end
    
    -- 3. Atos
    local atos = bot:FindItemSlot("item_rod_of_atos")
    if atos ~= nil and atos >= 0 and atos <= 5 and dist <= 1100 then
        local item = bot:GetItemInSlot(atos)
        if item and item:IsFullyCastable() then
            bot:Action_UseAbilityOnEntity(item, target)
            return true
        end
    end
    
    -- 4. Ethereal Blade / Veil of Discord
    local eth = bot:FindItemSlot("item_ethereal_blade") or bot:FindItemSlot("item_veil_of_discord")
    if eth ~= nil and eth >= 0 and eth <= 5 and dist <= 800 then
        local item = bot:GetItemInSlot(eth)
        if item and item:IsFullyCastable() then
            bot:Action_UseAbilityOnEntity(item, target)
            return true
        end
    end
    
    -- 5. Dagon (1-5)
    local dagon = bot:FindItemSlot("item_dagon") or bot:FindItemSlot("item_dagon_2") or bot:FindItemSlot("item_dagon_3") or bot:FindItemSlot("item_dagon_4") or bot:FindItemSlot("item_dagon_5")
    if dagon ~= nil and dagon >= 0 and dagon <= 5 and dist <= 800 then
        local item = bot:GetItemInSlot(dagon)
        if item and item:IsFullyCastable() and target:GetHealth() < 800 then
            bot:Action_UseAbilityOnEntity(item, target)
            return true
        end
    end
    
    return false
end

-- 3. DEFENSIVE ITEM AUTO-USE SYSTEM (Сэйв предметы в драке)
local function UseDefensiveItems(bot)
    local hp_pct = bot:GetHealth() / bot:GetMaxHealth()
    local bot_loc = bot:GetLocation()
    
    -- 1. Satanic pop at low health
    local satanic = bot:FindItemSlot("item_satanic")
    if satanic ~= nil and satanic >= 0 and satanic <= 5 and hp_pct < 0.35 then
        local item = bot:GetItemInSlot(satanic)
        if item and item:IsFullyCastable() then
            bot:ActionImmediate_UseAbility(item)
            print("[PRO_ITEM] Satanic activated to save core!")
            return true
        end
    end
    
    -- 2. BKB pop under heavy focus/spells
    local bkb = bot:FindItemSlot("item_black_king_bar")
    if bkb ~= nil and bkb >= 0 and bkb <= 5 then
        local item = bot:GetItemInSlot(bkb)
        if item and item:IsFullyCastable() then
            local nearby_enemies = bot:GetNearbyHeroes(800, true, BOT_MODE_NONE)
            if (nearby_enemies ~= nil and #nearby_enemies >= 2 and hp_pct < 0.45) or bot:HasModifier("modifier_silence") then
                bot:ActionImmediate_UseAbility(item)
                print("[PRO_ITEM] Black King Bar popped under threat!")
                return true
            end
        end
    end
    
    -- 3. Magic Wand/Stick
    local wand = bot:FindItemSlot("item_magic_wand") or bot:FindItemSlot("item_magic_stick")
    if wand ~= nil and wand >= 0 and wand <= 5 and hp_pct < 0.30 then
        local item = bot:GetItemInSlot(wand)
        if item and item:IsFullyCastable() and item:GetCurrentCharges() >= 10 then
            bot:ActionImmediate_UseAbility(item)
            return true
        end
    end
    
    -- 4. Guardian Greaves / Mekansm
    local msk = bot:FindItemSlot("item_guardian_greaves") or bot:FindItemSlot("item_mekansm")
    if msk ~= nil and msk >= 0 and msk <= 5 and hp_pct < 0.35 then
        local item = bot:GetItemInSlot(msk)
        if item and item:IsFullyCastable() then
            bot:ActionImmediate_UseAbility(item)
            return true
        end
    end
    
    return false
end

-- 4. SPELL PROJECTILE DODGER SYSTEM (Додж способностями)
local function DodgeEnemyProjectiles(bot)
    -- Puck's Phase Shift, Jugg's Blade Fury, Lifestealer's Rage, etc.
    local phase = bot:GetAbilityByName("puck_phase_shift")
    local fury = bot:GetAbilityByName("juggernaut_blade_fury")
    local rage = bot:GetAbilityByName("life_stealer_rage")
    
    if bot:WasRecentlyDamagedByAnyHero(0.2) or bot:HasModifier("modifier_projectile") then
        if phase and phase:IsFullyCastable() then
            bot:Action_UseAbility(phase)
            print("[DODGE_ABILITY] Puck used Phase Shift to dodge projectile!")
            return true
        elseif fury and fury:IsFullyCastable() then
            bot:Action_UseAbility(fury)
            print("[DODGE_ABILITY] Juggernaut used Blade Fury to dodge projectile!")
            return true
        elseif rage and rage:IsFullyCastable() then
            bot:Action_UseAbility(rage)
            print("[DODGE_ABILITY] Lifestealer used Rage to dodge projectile!")
            return true
        end
    end
    return false
end

function AbilityUseThink()
    local bot = GetBot()
    if bot == nil or not bot:IsAlive() or bot:IsChanneling() or bot:IsCastingAbility() then return end
    
    local bot_loc = bot:GetLocation()
    
    -- 1. Run Dodge System
    if DodgeEnemyProjectiles(bot) then return end
    
    -- 2. Run Defensive Items System
    if UseDefensiveItems(bot) then return end
    
    -- ============ CUSTOM SPECIALIZED CASTING LOGIC BY HERO ============
"""
        
        # Add hero-specific custom intelligence blocks
        if hero_short_name == "lina":
            lua_content += """
    local lsa = bot:GetAbilityByName("lina_light_strike_array")
    local slave = bot:GetAbilityByName("lina_dragon_slave")
    local laguna = bot:GetAbilityByName("lina_laguna_blade")
    
    local target = GetBestTarget(bot, 1000)
    if target ~= nil then
        -- Run Item Chaining first
        if UseOffensiveItems(bot, target) then return end
        
        local t_loc = target:GetLocation()
        local dist = GetDistance(bot_loc, t_loc)
        
        -- 1. Laguna Blade Kill Secure
        if laguna and laguna:IsFullyCastable() and dist <= 600 then
            local lag_dmg = 450
            local lvl = laguna:GetLevel()
            if lvl == 2 then lag_dmg = 650 elseif lvl == 3 then lag_dmg = 850 end
            
            -- Estimate damage after standard 25% magic resistance
            local actual_dmg = lag_dmg * 0.75
            if target:GetHealth() <= actual_dmg then
                bot:Action_UseAbilityOnEntity(laguna, target)
                print("[PRO_CAST] LINA popped Laguna Blade to secure kill!")
                return
            end
        end
        
        -- 2. Light Strike Array with predictive movement vector
        if lsa and lsa:IsFullyCastable() and dist <= 625 then
            if target:HasModifier("modifier_stunned") or target:HasModifier("modifier_rooted") then
                bot:Action_UseAbilityOnLocation(lsa, t_loc)
                return
            else
                -- Predict location based on velocity vector
                local pred_loc = t_loc + target:GetVelocity() * 0.5
                bot:Action_UseAbilityOnLocation(lsa, pred_loc)
                return
            end
        end
        
        -- 3. Dragon Slave area harass
        if slave and slave:IsFullyCastable() and dist <= 800 then
            bot:Action_UseAbilityOnLocation(slave, t_loc)
            return
        end
    end
"""
        elif hero_short_name == "nevermore":
            lua_content += """
    local raze1 = bot:GetAbilityByName("nevermore_shadow_raze1") -- Short (200)
    local raze2 = bot:GetAbilityByName("nevermore_shadow_raze2") -- Med (450)
    local raze3 = bot:GetAbilityByName("nevermore_shadow_raze3") -- Long (700)
    local requiem = bot:GetAbilityByName("nevermore_requiem")
    
    local target = GetBestTarget(bot, 900)
    if target ~= nil then
        -- Run Item Chaining first
        if UseOffensiveItems(bot, target) then return end
        
        local t_loc = target:GetLocation()
        local dist = GetDistance(bot_loc, t_loc)
        
        -- 1. Pop Requiem if 3+ enemies grouped close
        if requiem and requiem:IsFullyCastable() then
            local close_enemies = bot:GetNearbyHeroes(400, true, BOT_MODE_NONE)
            if close_enemies ~= nil and #close_enemies >= 3 then
                bot:Action_UseAbility(requiem)
                print("[PRO_CAST] NEVERMORE popped Requiem of Souls in center of group!")
                return
            end
        end
        
        -- 2. Tri-Raze combos on precise distances
        if dist < 280 and raze1 and raze1:IsFullyCastable() then
            bot:Action_UseAbility(raze1)
            print("[PRO_CAST] SF Short Raze hit!")
            return
        elseif dist >= 350 and dist <= 550 and raze2 and raze2:IsFullyCastable() then
            bot:Action_UseAbility(raze2)
            print("[PRO_CAST] SF Medium Raze hit!")
            return
        elseif dist >= 600 and dist <= 800 and raze3 and raze3:IsFullyCastable() then
            bot:Action_UseAbility(raze3)
            print("[PRO_CAST] SF Long Raze hit!")
            return
        end
    end
"""
        elif hero_short_name == "pudge":
            lua_content += """
    local hook = bot:GetAbilityByName("pudge_meat_hook")
    local rot = bot:GetAbilityByName("pudge_rot")
    local ult = bot:GetAbilityByName("pudge_dismember")
    
    local target = GetBestTarget(bot, 1300)
    if target ~= nil then
        local t_loc = target:GetLocation()
        local dist = GetDistance(bot_loc, t_loc)
        
        -- 1. Dismember lockdown
        if ult and ult:IsFullyCastable() and dist <= 200 then
            bot:Action_UseAbilityOnEntity(ult, target)
            return
        end
        
        -- 2. Rot toggler
        if rot then
            local is_active = rot:GetToggleState()
            if dist < 250 and not is_active then
                bot:ActionImmediate_ToggleAbility(rot)
            elseif dist > 320 and is_active then
                bot:ActionImmediate_ToggleAbility(rot)
            end
        end
        
        -- 3. Predictive Meat Hook
        if hook and hook:IsFullyCastable() and dist <= 1100 then
            local pred_loc = t_loc + target:GetVelocity() * 0.5
            bot:Action_UseAbilityOnLocation(hook, pred_loc)
            print("[PRO_CAST] PUDGE threw predictive Meat Hook!")
            return
        end
    end
"""
        elif hero_short_name == "juggernaut":
            lua_content += """
    local fury = bot:GetAbilityByName("juggernaut_blade_fury")
    local ward = bot:GetAbilityByName("juggernaut_healing_ward")
    local slash = bot:GetAbilityByName("juggernaut_omni_slash")
    
    local target = GetBestTarget(bot, 800)
    if target ~= nil then
        local t_loc = target:GetLocation()
        local dist = GetDistance(bot_loc, t_loc)
        
        -- 1. Smart Omnislash Creep-Avoidance check
        if slash and slash:IsFullyCastable() and dist <= 350 then
            local nearby_creeps = bot:GetNearbyCreeps(400, true)
            if nearby_creeps == nil or #nearby_creeps < 2 then
                bot:Action_UseAbilityOnEntity(slash, target)
                print("[PRO_CAST] JUGGERNAUT executed Omnislash with isolated target!")
                return
            end
        end
        
        -- 2. Blade Fury defense
        if fury and fury:IsFullyCastable() and dist <= 250 then
            local hp_pct = bot:GetHealth() / bot:GetMaxHealth()
            if hp_pct < 0.4 or bot:HasModifier("modifier_silence") or bot:HasModifier("modifier_rooted") then
                bot:Action_UseAbility(fury)
                return
            end
        end
        
        -- 3. Healing Ward in combat
        if ward and ward:IsFullyCastable() then
            local hp_pct = bot:GetHealth() / bot:GetMaxHealth()
            if hp_pct < 0.5 then
                bot:Action_UseAbilityOnLocation(ward, bot_loc)
                return
            end
        end
    end
"""
        elif hero_short_name == "crystal_maiden":
            lua_content += """
    local nova = bot:GetAbilityByName("crystal_maiden_crystal_nova")
    local bite = bot:GetAbilityByName("crystal_maiden_frostbite")
    local field = bot:GetAbilityByName("crystal_maiden_freezing_field")
    
    local target = GetBestTarget(bot, 900)
    if target ~= nil then
        local t_loc = target:GetLocation()
        local dist = GetDistance(bot_loc, t_loc)
        
        -- 1. Freezing Field during group fights
        if field and field:IsFullyCastable() and dist <= 600 then
            local close_enemies = bot:GetNearbyHeroes(700, true, BOT_MODE_NONE)
            if close_enemies ~= nil and #close_enemies >= 2 then
                -- Pop Glimmer or BKB if CM has it to protect Freezing Field channel!
                local gl = bot:FindItemSlot("item_glimmer_cape")
                if gl ~= nil and gl >= 0 then
                    local gl_item = bot:GetItemInSlot(gl)
                    if gl_item and gl_item:IsFullyCastable() then
                        bot:ActionImmediate_UseAbility(gl_item)
                    end
                end
                bot:Action_UseAbility(field)
                print("[PRO_CAST] CM popped Freezing Field!")
                return
            end
        end
        
        -- 2. Frostbite single target hold
        if bite and bite:IsFullyCastable() and dist <= 550 then
            bot:Action_UseAbilityOnEntity(bite, target)
            return
        end
        
        -- 3. Crystal Nova slow
        if nova and nova:IsFullyCastable() and dist <= 700 then
            bot:Action_UseAbilityOnLocation(nova, t_loc)
            return
        end
    end
"""
        else:
            # DYNAMIC GENERIC AUTO-CASTER FOR ALL OTHER HEROES (Умный автокастер)
            lua_content += f"""
    -- Target selection via Vulnerability Scoring
    local target = GetBestTarget(bot, 1000)
    if target ~= nil then
        -- Pop offensive active item combos first
        if UseOffensiveItems(bot, target) then return end
        
        local t_loc = target:GetLocation()
        
        -- Auto-Caster scanning slots dynamically for basic abilities
        for slot = 0, 2 do
            local abil = bot:GetAbilityInSlot(slot)
            if abil and abil:IsFullyCastable() then
                local range = abil:GetCastRange()
                if range == 0 or range > 1200 then range = 600 end
                
                local dist = GetDistance(bot_loc, t_loc)
                if dist <= (range + 100) then
                    -- Check targeting type dynamically
                    local behavior = abil:GetBehavior()
                    if (behavior & 8) ~= 0 then -- UNIT TARGET
                        bot:Action_UseAbilityOnEntity(abil, target)
                        return
                    elseif (behavior & 16) ~= 0 then -- POINT TARGET
                        bot:Action_UseAbilityOnLocation(abil, t_loc)
                        return
                    elseif (behavior & 4) ~= 0 then -- NO TARGET
                        bot:Action_UseAbility(abil)
                        return
                    end
                end
            end
        end
        
        -- Dynamic Ultimate pop
        local ult = bot:GetAbilityInSlot(5)
        if ult and ult:IsFullyCastable() then
            local range = ult:GetCastRange()
            if range == 0 or range > 1200 then range = 600 end
            
            local dist = GetDistance(bot_loc, t_loc)
            if dist <= range then
                local behavior = ult:GetBehavior()
                if (behavior & 8) ~= 0 then
                    bot:Action_UseAbilityOnEntity(ult, target)
                    return
                elseif (behavior & 16) ~= 0 then
                    bot:Action_UseAbilityOnLocation(ult, t_loc)
                    return
                elseif (behavior & 4) ~= 0 then
                    bot:Action_UseAbility(ult)
                    return
                end
            end
        end
    end
"""
        
        lua_content += """
end
"""
        
        # Write individual file
        file_path = os.path.join(DOTA_VSCRIPTS_BOTS_DIR, f"ability_item_usage_{hero_short_name}.lua")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(lua_content)
            generated_count += 1
        except Exception as e:
            print(f"[ERROR] Writing file for {hero_short_name} failed: {e}")
            
    print(f"\n=== Successfully generated dedicated scripts for ALL {generated_count} heroes in Steam directory! ===")

if __name__ == "__main__":
    main()
