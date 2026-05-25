import os
import requests
import json
import time

API_KEY = "deb3dc65-2e3a-4c9e-9d16-bce6ff480468"
OUTPUT_LUA_PATH = r"C:\бот\ability_item_usage_generic.lua"
DOTA_VSCRIPTS_BOTS_DIR = r"C:\stea\steamapps\common\dota 2 beta\game\dota\scripts\vscripts\bots"

def get_heroes():
    print("Fetching hero list from OpenDota...")
    url = f"https://api.opendota.com/api/heroes?api_key={API_KEY}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching heroes: {e}")
        return []

def get_hero_abilities_mapping():
    print("Fetching hero abilities mapping from dotaconstants...")
    url = "https://raw.githubusercontent.com/odota/dotaconstants/master/build/hero_abilities.json"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching hero abilities: {e}")
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

def generate_lua_ability_builds():
    heroes = get_heroes()
    abilities_map = get_hero_abilities_mapping()
    
    if not heroes or not abilities_map:
        print("Failed to load required data from API.")
        return

    lua_builds = {}
    
    for hero in heroes:
        hero_name = hero['name']  # e.g., npc_dota_hero_antimage
        abilities_info = abilities_map.get(hero_name, {})
        
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
                "shadow_shaman_mass_serpent_ward", "nevermore_requiem", "lina_laguna_blade",
                "phantom_assassin_coup_de_grace", "zuus_thundergods_wrath", "warlock_rain_of_chaos",
                "faceless_void_chronosphere", "tidehunter_ravage", "enigma_black_hole"
            ]:
                ultimate = abil
            elif len(real_basics) < 3:
                real_basics.append(abil)
        
        # Fallback if no explicit ultimate detected
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
        
        std_build = []
        aggr_build = []
        
        # Standard Levels (1 to 30)
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
                
        # Aggressive Levels (1 to 30)
        for level in range(1, 31):
            if level in [6, 12, 18]:
                aggr_build.append(ultimate)
            elif level == 10:
                aggr_build.append(talents[1] if len(talents) > 1 else t10)
            elif level == 15:
                aggr_build.append(talents[3] if len(talents) > 3 else t15)
            elif level == 20:
                aggr_build.append(talents[5] if len(talents) > 5 else t20)
            elif level == 25:
                aggr_build.append(talents[7] if len(talents) > 7 else t25)
            elif level in [1, 2, 4, 7]:
                aggr_build.append(real_basics[1])
            elif level in [3, 5, 8, 9]:
                aggr_build.append(real_basics[0])
            elif level in [11, 13, 14, 16]:
                aggr_build.append(real_basics[2])
            else:
                aggr_build.append("special_bonus_attributes")
                
        lua_builds[hero_name] = {
            'standard': std_build,
            'aggressive': aggr_build
        }

    # Generate Lua file
    lua_content = """-- ============================================================================
-- ability_item_usage_generic.lua — DYNAMIC ability leveling for all AI heroes
-- ============================================================================
-- Automatically compiled using real-time OpenDota and dotaconstants API data.
-- Standard and Aggressive/Support capability leveling profiles for all 127+ heroes.
-- Supports custom talents, attribute upgrades, and dynamic selection.
-- ============================================================================

local ABILITY_BUILDS_STANDARD = {
"""
    for hero_name, builds in sorted(lua_builds.items()):
        lua_content += f"    [\"{hero_name}\"] = {{\n"
        for abil in builds['standard']:
            lua_content += f'        "{abil}",\n'
        lua_content += "    },\n"
    lua_content += "}\n\n"

    lua_content += "local ABILITY_BUILDS_AGGRESSIVE = {\n"
    for hero_name, builds in sorted(lua_builds.items()):
        lua_content += f"    [\"{hero_name}\"] = {{\n"
        for abil in builds['aggressive']:
            lua_content += f'        "{abil}",\n'
        lua_content += "    },\n"
    lua_content += "}\n\n"

    lua_content += """-- Generic fallback build just in case
local DEFAULT_BUILD = {
    "special_bonus_attributes", "special_bonus_attributes", "special_bonus_attributes",
    "special_bonus_attributes", "special_bonus_attributes", "special_bonus_attributes",
    "special_bonus_attributes", "special_bonus_attributes", "special_bonus_attributes",
    "special_bonus_attributes", "special_bonus_attributes", "special_bonus_attributes",
    "special_bonus_attributes", "special_bonus_attributes", "special_bonus_attributes",
    "special_bonus_attributes", "special_bonus_attributes", "special_bonus_attributes",
    "special_bonus_attributes", "special_bonus_attributes", "special_bonus_attributes",
    "special_bonus_attributes", "special_bonus_attributes", "special_bonus_attributes",
    "special_bonus_attributes", "special_bonus_attributes", "special_bonus_attributes",
    "special_bonus_attributes", "special_bonus_attributes", "special_bonus_attributes"
}

function AbilityLevelUpThink()
    local bot = GetBot()
    if bot == nil or bot:GetAbilityPoints() <= 0 then
        return
    end

    local hero_name = bot:GetUnitName()
    local level = bot:GetLevel()
    
    -- Choose build type based on role (supports/mid choose aggressive/support build)
    local build_type = "standard"
    local pos = 1
    if _G.GetBotPosition ~= nil then
        pos = _G.GetBotPosition(bot)
    end
    
    if pos == 2 or pos == 4 or pos == 5 then
        build_type = "aggressive"
    end
    
    local build = ABILITY_BUILDS_STANDARD[hero_name]
    if build_type == "aggressive" and ABILITY_BUILDS_AGGRESSIVE[hero_name] ~= nil then
        build = ABILITY_BUILDS_AGGRESSIVE[hero_name]
    end
    
    if build == nil then
        build = DEFAULT_BUILD
    end
    
    local ability_name = build[level]
    if ability_name ~= nil and ability_name ~= "special_bonus_attributes" and ability_name ~= "generic_hidden" then
        local abil = bot:GetAbilityByName(ability_name)
        if abil ~= nil and abil:CanAbilityBeUpgraded() then
            bot:ActionImmediate_LevelAbility(ability_name)
            print(string.format("[BOT_ABILITIES] ID:%d | %s leveled ability %s at level %d (%s)!", 
                bot:GetPlayerID(), hero_name, ability_name, level, build_type))
            return
        end
    end
    
    -- Fallback: Level up any available basic ability or ultimate
    local ult = bot:GetAbilityInSlot(5)
    if ult and ult:CanAbilityBeUpgraded() and ult:GetLevel() < ult:GetMaxLevel() then
        bot:ActionImmediate_LevelAbility(ult:GetName())
        return
    end
    
    for i = 6, 23 do
        local abil = bot:GetAbilityInSlot(i)
        if abil and abil:CanAbilityBeUpgraded() then
            local name = abil:GetName()
            if name and string.find(name, "special_bonus_") then
                bot:ActionImmediate_LevelAbility(name)
                return
            end
        end
    end
    
    for i = 0, 2 do
        local abil = bot:GetAbilityInSlot(i)
        if abil and abil:CanAbilityBeUpgraded() and abil:GetLevel() < abil:GetMaxLevel() then
            bot:ActionImmediate_LevelAbility(abil:GetName())
            return
        end
    end
    
    -- Level stats if nothing else is upgradable
    local stats = bot:GetAbilityByName("special_bonus_attributes")
    if stats and stats:CanAbilityBeUpgraded() then
        bot:ActionImmediate_LevelAbility("special_bonus_attributes")
    end
end

function AbilityUseThink()
    -- Native C++ engine handles spell usage and active combats, leaving macro movement overlays to Think()
end
"""

    with open(OUTPUT_LUA_PATH, "w", encoding="utf-8") as f:
        f.write(lua_content)
    print(f"Successfully generated dynamic ability upgrade script at {OUTPUT_LUA_PATH}")

    # Copy to steam directory
    if os.path.exists(DOTA_VSCRIPTS_BOTS_DIR):
        dst_path = os.path.join(DOTA_VSCRIPTS_BOTS_DIR, "ability_item_usage_generic.lua")
        try:
            import shutil
            shutil.copy2(OUTPUT_LUA_PATH, dst_path)
            print(f"Successfully deployed ability builds directly to Steam client: {dst_path}")
        except Exception as e:
            print(f"Error deploying ability build script: {e}")

if __name__ == "__main__":
    generate_lua_ability_builds()
