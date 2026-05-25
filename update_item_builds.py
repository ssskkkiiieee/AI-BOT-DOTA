import os
import requests
import json
import time
import shutil

API_KEY = "deb3dc65-2e3a-4c9e-9d16-bce6ff480468"
DOTA_VSCRIPTS_BOTS_DIR = r"C:\stea\steamapps\common\dota 2 beta\game\dota\scripts\vscripts\bots"
OUTPUT_LUA_PATH = r"C:\бот\item_purchase_generic.lua"

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

def get_item_popularity(hero_id):
    url = f"https://api.opendota.com/api/heroes/{hero_id}/itemPopularity?api_key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def get_item_ids_mapping():
    print("Fetching item ID mapping from dotaconstants...")
    url = "https://raw.githubusercontent.com/odota/dotaconstants/master/build/item_ids.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching item mapping: {e}")
    return {}

def get_top_items(item_dict, item_id_map, limit=4, skip_items=None):
    if not item_dict:
        return []
    ignored_items = {
        'item_tpscroll', 'item_ward_observer', 'item_ward_sentry', 
        'item_smoke_of_deceit', 'item_dust', 'item_infused_raindrop', 
        'item_aegis', 'item_ward_dispenser', 'item_clarity', 
        'item_flask', 'item_enchanted_mango', 'item_tango'
    }
    if skip_items:
        ignored_items.update(skip_items)
    
    translated_items = {}
    for item_id, count in item_dict.items():
        item_name = item_id_map.get(str(item_id))
        if item_name:
            if not item_name.startswith("item_"):
                item_name = "item_" + item_name
            translated_items[item_name] = count
            
    sorted_items = sorted(translated_items.items(), key=lambda x: x[1], reverse=True)
    filtered = [item for item, count in sorted_items if item not in ignored_items]
    return filtered[:limit]

def build_sequential_items_standard(popularity_data, item_id_map):
    if not popularity_data:
        return []
    build = ["item_tango", "item_branches", "item_branches"]
    build.extend(get_top_items(popularity_data.get('start_game_items'), item_id_map, limit=2))
    build.extend(get_top_items(popularity_data.get('early_game_items'), item_id_map, limit=3))
    build.extend(get_top_items(popularity_data.get('mid_game_items'), item_id_map, limit=3))
    build.extend(get_top_items(popularity_data.get('late_game_items'), item_id_map, limit=3))
    return build

def build_sequential_items_aggressive(popularity_data, item_id_map):
    if not popularity_data:
        return []
    build = ["item_tango", "item_branches", "item_faerie_fire"]
    build.extend(get_top_items(popularity_data.get('start_game_items'), item_id_map, limit=3))
    build.extend(get_top_items(popularity_data.get('early_game_items'), item_id_map, limit=3))
    # Offensive high damage/mobility focus
    standard_mid = get_top_items(popularity_data.get('mid_game_items'), item_id_map, limit=3)
    all_mid = get_top_items(popularity_data.get('mid_game_items'), item_id_map, limit=6)
    aggr_mid = [x for x in all_mid if x not in standard_mid] or all_mid[:3]
    build.extend(aggr_mid[:3])
    
    standard_late = get_top_items(popularity_data.get('late_game_items'), item_id_map, limit=3)
    all_late = get_top_items(popularity_data.get('late_game_items'), item_id_map, limit=6)
    aggr_late = [x for x in all_late if x not in standard_late] or all_late[:3]
    build.extend(aggr_late[:3])
    return build

def build_sequential_items_support(popularity_data, item_id_map):
    if not popularity_data:
        return []
    build = ["item_tango", "item_branches", "item_blood_grenade"]
    # Support and team utility items
    support_items = {
        'item_urn_of_shadows', 'item_glimmer_cape', 'item_force_staff', 
        'item_arcane_boots', 'item_mekansm', 'item_guardian_greaves', 
        'item_pipe', 'item_lotus_orb', 'item_vladmir', 'item_solar_crest',
        'item_aeon_disk', 'item_eul', 'item_wind_waker', 'item_aether_lens'
    }
    
    # Start
    start = get_top_items(popularity_data.get('start_game_items'), item_id_map, limit=3)
    build.extend(start)
    
    # Early
    early = get_top_items(popularity_data.get('early_game_items'), item_id_map, limit=3)
    build.extend(early)
    
    # Mid/Late filtered to support items
    mid_late = []
    for section in ('mid_game_items', 'late_game_items'):
        section_data = popularity_data.get(section)
        if section_data:
            for item_id in section_data.keys():
                item_name = item_id_map.get(str(item_id))
                if item_name:
                    if not item_name.startswith("item_"):
                        item_name = "item_" + item_name
                    if item_name in support_items and item_name not in build:
                        mid_late.append(item_name)
                        
    if len(mid_late) < 6:
        # Fallback to general popular items if support items are scarce
        mid_late.extend(get_top_items(popularity_data.get('mid_game_items'), item_id_map, limit=4))
        mid_late.extend(get_top_items(popularity_data.get('late_game_items'), item_id_map, limit=4))
        
    # Remove duplicates
    seen = set(build)
    unique_mid_late = []
    for x in mid_late:
        if x not in seen:
            seen.add(x)
            unique_mid_late.append(x)
            
    build.extend(unique_mid_late[:6])
    return build

def build_sequential_items_turtle(popularity_data, item_id_map):
    if not popularity_data:
        return []
    build = ["item_tango", "item_branches", "item_branches"]
    # Defensive/Tanky items focus
    turtle_items = {
        'item_bracer', 'item_vanguard', 'item_pipe', 'item_crimson_guard',
        'item_blade_mail', 'item_aeon_disk', 'item_heart', 'item_satanic',
        'item_shivas_guard', 'item_assault', 'item_black_king_bar', 'item_lotus_orb',
        'item_heavens_halberd', 'item_linkens'
    }
    
    # Start
    start = get_top_items(popularity_data.get('start_game_items'), item_id_map, limit=3)
    build.extend(start)
    
    # Early
    early = get_top_items(popularity_data.get('early_game_items'), item_id_map, limit=3)
    build.extend(early)
    
    # Mid/Late filtered to turtle items
    mid_late = []
    for section in ('mid_game_items', 'late_game_items'):
        section_data = popularity_data.get(section)
        if section_data:
            for item_id in section_data.keys():
                item_name = item_id_map.get(str(item_id))
                if item_name:
                    if not item_name.startswith("item_"):
                        item_name = "item_" + item_name
                    if item_name in turtle_items and item_name not in build:
                        mid_late.append(item_name)
                        
    if len(mid_late) < 6:
        mid_late.extend(get_top_items(popularity_data.get('mid_game_items'), item_id_map, limit=4))
        mid_late.extend(get_top_items(popularity_data.get('late_game_items'), item_id_map, limit=4))
        
    seen = set(build)
    unique_mid_late = []
    for x in mid_late:
        if x not in seen:
            seen.add(x)
            unique_mid_late.append(x)
            
    build.extend(unique_mid_late[:6])
    return build

def main():
    print("=== Updating Dynamic Quad-Build Item Purchases via OpenDota API ===")
    
    heroes = get_heroes()
    if not heroes:
        print("Failed to retrieve hero list.")
        return

    item_id_map = get_item_ids_mapping()
    standard_builds = {}
    aggressive_builds = {}
    support_builds = {}
    turtle_builds = {}
    
    total = len(heroes)
    for i, hero in enumerate(heroes):
        hero_name = hero['name']  # npc_dota_hero_antimage
        hero_id = hero['id']
        
        print(f"[{i+1}/{total}] Fetching dynamic quad item builds for {hero_name}...")
        pop_data = get_item_popularity(hero_id)
        
        std = build_sequential_items_standard(pop_data, item_id_map)
        agg = build_sequential_items_aggressive(pop_data, item_id_map)
        sup = build_sequential_items_support(pop_data, item_id_map)
        tur = build_sequential_items_turtle(pop_data, item_id_map)
        
        default_build = [
            "item_tango", "item_branches", "item_branches", "item_magic_stick",
            "item_boots", "item_gloves", "item_boots_of_elves", "item_ogre_axe",
            "item_mithril_hammer", "item_black_king_bar"
        ]
        
        standard_builds[hero_name] = std if std else default_build
        aggressive_builds[hero_name] = agg if agg else default_build
        support_builds[hero_name] = sup if sup else default_build
        turtle_builds[hero_name] = tur if tur else default_build
            
        time.sleep(0.12)  # Avoid rate-limiting

    # Generate Lua file
    lua_content = """-- ============================================================================
-- item_purchase_generic.lua — QUAD-BUILD dynamic item purchase script
-- ============================================================================
-- Automatically compiled using real-time OpenDota professional match data.
-- 4 builds per hero: Standard, Aggressive, Support, Turtle.
-- Features real-time adaptive counter-picks, BKB skipping, secret shop navigation,
-- slot management (selling starter items), Moon Shard and Blink upgrades!
-- ============================================================================

local ITEM_BUILDS_STANDARD = {
"""
    for hero_name, build in sorted(standard_builds.items()):
        lua_content += f"    {hero_name} = {{\n"
        for item in build:
            lua_content += f'        "{item}",\n'
        lua_content += "    },\n"
    lua_content += "}\n\n"

    lua_content += "local ITEM_BUILDS_AGGRESSIVE = {\n"
    for hero_name, build in sorted(aggressive_builds.items()):
        lua_content += f"    {hero_name} = {{\n"
        for item in build:
            lua_content += f'        "{item}",\n'
        lua_content += "    },\n"
    lua_content += "}\n\n"

    lua_content += "local ITEM_BUILDS_SUPPORT = {\n"
    for hero_name, build in sorted(support_builds.items()):
        lua_content += f"    {hero_name} = {{\n"
        for item in build:
            lua_content += f'        "{item}",\n'
        lua_content += "    },\n"
    lua_content += "}\n\n"

    lua_content += "local ITEM_BUILDS_TURTLE = {\n"
    for hero_name, build in sorted(turtle_builds.items()):
        lua_content += f"    {hero_name} = {{\n"
        for item in build:
            lua_content += f'        "{item}",\n'
        lua_content += "    },\n"
    lua_content += "}\n\n"

    lua_content += """local DEFAULT_BUILD = {
    "item_tango",
    "item_branches",
    "item_branches",
    "item_magic_stick",
    "item_boots",
    "item_gloves",
    "item_boots_of_elves",
    "item_ogre_axe",
    "item_mithril_hammer",
    "item_black_king_bar",
}

local purchase_index = {}
local selected_build_type = {}

-- Profile matchups lists
local ESCAPE_HEROES = {
    ["npc_dota_hero_antimage"] = true, ["npc_dota_hero_queenofpain"] = true,
    ["npc_dota_hero_puck"] = true, ["npc_dota_hero_weaver"] = true,
    ["npc_dota_hero_storm_spirit"] = true, ["npc_dota_hero_void_spirit"] = true,
    ["npc_dota_hero_clinkz"] = true, ["npc_dota_hero_riki"] = true,
    ["npc_dota_hero_bounty_hunter"] = true, ["npc_dota_hero_mirana"] = true,
    ["npc_dota_hero_slark"] = true
}

local HEAL_HEROES = {
    ["npc_dota_hero_huskar"] = true, ["npc_dota_hero_morphling"] = true,
    ["npc_dota_hero_lifestealer"] = true, ["npc_dota_hero_necrolyte"] = true,
    ["npc_dota_hero_alchemist"] = true, ["npc_dota_hero_dazzle"] = true,
    ["npc_dota_hero_witch_doctor"] = true, ["npc_dota_hero_abaddon"] = true,
    ["npc_dota_hero_wisp"] = true, ["npc_dota_hero_omniknight"] = true
}

local MAGIC_BURST_HEROES = {
    ["npc_dota_hero_zeus"] = true, ["npc_dota_hero_lina"] = true,
    ["npc_dota_hero_skywrath_mage"] = true, ["npc_dota_hero_lion"] = true,
    ["npc_dota_hero_tinker"] = true, ["npc_dota_hero_invoker"] = true,
    ["npc_dota_hero_pugna"] = true, ["npc_dota_hero_techies"] = true,
    ["npc_dota_hero_crystal_maiden"] = true, ["npc_dota_hero_leshrac"] = true
}

local DURABLE_HEROES = {
    ["npc_dota_hero_axe"] = true, ["npc_dota_hero_shredder"] = true,
    ["npc_dota_hero_dragon_knight"] = true, ["npc_dota_hero_centaur"] = true,
    ["npc_dota_hero_tidehunter"] = true, ["npc_dota_hero_bristleback"] = true,
    ["npc_dota_hero_underlord"] = true, ["npc_dota_hero_sven"] = true,
    ["npc_dota_hero_pudge"] = true
}

local SUPPORT_HEROES = {
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
}

local INVIS_HEROES = {
    ["npc_dota_hero_riki"] = true, ["npc_dota_hero_bounty_hunter"] = true,
    ["npc_dota_hero_clinkz"] = true, ["npc_dota_hero_nyx_assassin"] = true,
    ["npc_dota_hero_weaver"] = true, ["npc_dota_hero_sand_king"] = true,
    ["npc_dota_hero_mirana"] = true, ["npc_dota_hero_treant"] = true,
    ["npc_dota_hero_invoker"] = true
}


-- Agility Heroes (for Swift Blink)
local AGI_HEROES = {
    ["npc_dota_hero_antimage"] = true, ["npc_dota_hero_bloodseeker"] = true,
    ["npc_dota_hero_bounty_hunter"] = true, ["npc_dota_hero_broodmother"] = true,
    ["npc_dota_hero_clinkz"] = true, ["npc_dota_hero_drow_ranger"] = true,
    ["npc_dota_hero_ember_spirit"] = true, ["npc_dota_hero_faceless_void"] = true,
    ["npc_dota_hero_gyrocopter"] = true, ["npc_dota_hero_hoodwink"] = true,
    ["npc_dota_hero_juggernaut"] = true, ["npc_dota_hero_kez"] = true,
    ["npc_dota_hero_luna"] = true, ["npc_dota_hero_medusa"] = true,
    ["npc_dota_hero_meepo"] = true, ["npc_dota_hero_mirana"] = true,
    ["npc_dota_hero_monkey_king"] = true, ["npc_dota_hero_morphling"] = true,
    ["npc_dota_hero_naga_siren"] = true, ["npc_dota_hero_nyx_assassin"] = true,
    ["npc_dota_hero_pangolier"] = true, ["npc_dota_hero_phantom_assassin"] = true,
    ["npc_dota_hero_phantom_lancer"] = true, ["npc_dota_hero_razor"] = true,
    ["npc_dota_hero_riki"] = true, ["npc_dota_hero_shadow_fiend"] = true,
    ["npc_dota_hero_slark"] = true, ["npc_dota_hero_sniper"] = true,
    ["npc_dota_hero_spectre"] = true, ["npc_dota_hero_templar_assassin"] = true,
    ["npc_dota_hero_terrorblade"] = true, ["npc_dota_hero_troll_warlord"] = true,
    ["npc_dota_hero_ursa"] = true, ["npc_dota_hero_vengefulspirit"] = true,
    ["npc_dota_hero_viper"] = true, ["npc_dota_hero_weaver"] = true
}

-- Intelligence Heroes (for Arcane Blink)
local INT_HEROES = {
    ["npc_dota_hero_ancient_apparition"] = true, ["npc_dota_hero_bane"] = true,
    ["npc_dota_hero_batrider"] = true, ["npc_dota_hero_chen"] = true,
    ["npc_dota_hero_crystal_maiden"] = true, ["npc_dota_hero_dark_seer"] = true,
    ["npc_dota_hero_dark_willow"] = true, ["npc_dota_hero_dazzle"] = true,
    ["npc_dota_hero_death_prophet"] = true, ["npc_dota_hero_disruptor"] = true,
    ["npc_dota_hero_enigma"] = true, ["npc_dota_hero_grimstroke"] = true,
    ["npc_dota_hero_invoker"] = true, ["npc_dota_hero_jakiro"] = true,
    ["npc_dota_hero_keeper_of_the_light"] = true, ["npc_dota_hero_leshrac"] = true,
    ["npc_dota_hero_lich"] = true, ["npc_dota_hero_lina"] = true,
    ["npc_dota_hero_lion"] = true, ["npc_dota_hero_muerta"] = true,
    ["npc_dota_hero_nature_prophet"] = true, ["npc_dota_hero_necrolyte"] = true,
    ["npc_dota_hero_oracle"] = true, ["npc_dota_hero_outworld_odyssey"] = true,
    ["npc_dota_hero_puck"] = true, ["npc_dota_hero_pugna"] = true,
    ["npc_dota_hero_queenofpain"] = true, ["npc_dota_hero_rubick"] = true,
    ["npc_dota_hero_shadow_demon"] = true, ["npc_dota_hero_shadow_shaman"] = true,
    ["npc_dota_hero_silencer"] = true, ["npc_dota_hero_skywrath_mage"] = true,
    ["npc_dota_hero_storm_spirit"] = true, ["npc_dota_hero_techies"] = true,
    ["npc_dota_hero_tinker"] = true, ["npc_dota_hero_visage"] = true,
    ["npc_dota_hero_void_spirit"] = true, ["npc_dota_hero_warlock"] = true,
    ["npc_dota_hero_windrunner"] = true, ["npc_dota_hero_winter_wyvern"] = true,
    ["npc_dota_hero_witch_doctor"] = true, ["npc_dota_hero_zuus"] = true
}

local function EvaluateEnemyLineup()
    local escape = false
    local heal = false
    local magic = false
    local durable = false
    
    local enemy_team = GetOpposingTeam()
    local enemy_ids = GetTeamPlayers(enemy_team)
    
    for _, id in ipairs(enemy_ids) do
        local hero = GetSelectedHeroName(id)
        if hero then
            if ESCAPE_HEROES[hero] then escape = true end
            if HEAL_HEROES[hero] then heal = true end
            if MAGIC_BURST_HEROES[hero] then magic = true end
            if DURABLE_HEROES[hero] then durable = true end
        end
    end
    return escape, heal, magic, durable
end

-- Helper to find slot index of starting items to sell
local function FindItemSlotToSell(bot)
    local starter_items = {
        "item_branches", "item_circlet", "item_magic_stick", 
        "item_faerie_fire", "item_quelling_blade"
    }
    for _, name in ipairs(starter_items) do
        local slot = bot:FindItemSlot(name)
        if slot ~= nil and slot >= 0 and slot <= 5 then
            return slot
        end
    end
    return -1
end

function ItemPurchaseThink()
    local bot = GetBot()
    if bot == nil then return end

    local hero_name = bot:GetUnitName()
    local pid = bot:GetPlayerID()

    local escape, heal, magic, durable = EvaluateEnemyLineup()
    
    -- Dynamic role and situation selection
    if selected_build_type[pid] == nil then
        if SUPPORT_HEROES[hero_name] then
            selected_build_type[pid] = "support"
        elseif bot:GetAssignedLane() == 1 then -- Offlaner
            selected_build_type[pid] = "turtle"
        elseif durable then
            selected_build_type[pid] = "aggressive"
        else
            selected_build_type[pid] = "standard"
        end
        print(string.format("[BOT_PURCHASE] ID:%d | HERO:%s | Selected profile: %s", pid, hero_name, selected_build_type[pid]))
    end

    -- Adaptive Defensive trigger: if bot is dying too much (deaths >= 5), switch to Turtle build!
    local deaths = GetHeroDeaths(pid)
    if deaths >= 5 and selected_build_type[pid] ~= "turtle" and not SUPPORT_HEROES[hero_name] then
        selected_build_type[pid] = "turtle"
        bot.purchase_queue = nil -- Force queue reconstruction
        print(string.format("[BOT_PURCHASE] ID:%d | %s died %d times. Switching to TURTLE build for maximum defense!", pid, hero_name, deaths))
    end

    local base_build = ITEM_BUILDS_STANDARD[hero_name]
    if selected_build_type[pid] == "aggressive" then
        base_build = ITEM_BUILDS_AGGRESSIVE[hero_name] or ITEM_BUILDS_STANDARD[hero_name]
    elseif selected_build_type[pid] == "support" then
        base_build = ITEM_BUILDS_SUPPORT[hero_name] or ITEM_BUILDS_STANDARD[hero_name]
    elseif selected_build_type[pid] == "turtle" then
        base_build = ITEM_BUILDS_TURTLE[hero_name] or ITEM_BUILDS_STANDARD[hero_name]
    end

    if base_build == nil then
        base_build = DEFAULT_BUILD
    end

    -- Construct dynamic item list for this session
    if bot.purchase_queue == nil then
        bot.purchase_queue = {}
        for _, item in ipairs(base_build) do
            table.insert(bot.purchase_queue, item)
        end
        
        -- Insert counter items dynamically (after boots, index 5-6)
        local insert_pos = 5
        if #bot.purchase_queue < 5 then insert_pos = #bot.purchase_queue end
        
        -- Escape counter (Orchid/Sheepstick)
        if escape then
            if not SUPPORT_HEROES[hero_name] then
                table.insert(bot.purchase_queue, insert_pos, "item_orchid")
                print(string.format("[BOT_PURCHASE] ID:%d | HERO:%s counter-buying Orchid against escape heroes!", pid, hero_name))
            end
        end
        
        -- Healing/Regen counter (Vessel/Skadi)
        if heal then
            if SUPPORT_HEROES[hero_name] then
                table.insert(bot.purchase_queue, insert_pos, "item_spirit_vessel")
                print(string.format("[BOT_PURCHASE] ID:%d | Support %s counter-buying Spirit Vessel against healing heroes!", pid, hero_name))
            else
                table.insert(bot.purchase_queue, insert_pos, "item_eye_of_skadi")
                print(string.format("[BOT_PURCHASE] ID:%d | Core %s counter-buying Eye of Skadi against healing heroes!", pid, hero_name))
            end
        end

        -- Durable Tank counter (Desolator)
        if durable and not SUPPORT_HEROES[hero_name] then
            table.insert(bot.purchase_queue, insert_pos, "item_desolator")
            print(string.format("[BOT_PURCHASE] ID:%d | Core %s counter-buying Desolator against tanky heroes!", pid, hero_name))
        end

        -- BKB skipping if no magic threats
        if not magic then
            for idx = #bot.purchase_queue, 1, -1 do
                local name = bot.purchase_queue[idx]
                if name == "item_black_king_bar" or name == "item_recipe_black_king_bar" or name == "item_bkb" then
                    table.remove(bot.purchase_queue, idx)
                    print(string.format("[BOT_PURCHASE] ID:%d | %s SKIPPING Black King Bar (lack of enemy magic threats)!", pid, hero_name))
                end
            end
        end
    end

    -- ========================================================================
    -- TOME OF KNOWLEDGE AUTO-PURCHASE (supports only, every 10 min)
    -- ========================================================================
    if _G.tome_purchase_tracker == nil then _G.tome_purchase_tracker = {} end
    if SUPPORT_HEROES[hero_name] then
        local game_time = DotaTime()
        local last_tome_time = _G.tome_purchase_tracker[pid] or -9999
        if game_time > 600 then
            -- Calculate average enemy hero level
            local enemy_team = GetOpposingTeam()
            local enemy_ids = GetTeamPlayers(enemy_team)
            local total_enemy_level = 0
            local enemy_count = 0
            for _, eid in ipairs(enemy_ids) do
                if IsHeroAlive(eid) then
                    local elevel = GetHeroLevel(eid)
                    if elevel and elevel > 0 then
                        total_enemy_level = total_enemy_level + elevel
                        enemy_count = enemy_count + 1
                    end
                end
            end
            local avg_enemy_level = 1
            if enemy_count > 0 then
                avg_enemy_level = total_enemy_level / enemy_count
            end
            local my_level = bot:GetLevel()
            local gold = bot:GetGold()
            local tome_cooldown_ok = (game_time - last_tome_time) >= 600
            if my_level < avg_enemy_level and gold >= 75 and tome_cooldown_ok then
                bot:ActionImmediate_PurchaseItem("item_tome_of_knowledge")
                _G.tome_purchase_tracker[pid] = game_time
                print(string.format("[TOME] ID:%d | %s bought Tome of Knowledge! MyLvl:%d < AvgEnemyLvl:%.1f | Gold:%d | GameTime:%.0f",
                    pid, hero_name, my_level, avg_enemy_level, gold, game_time))
            end
        end
    end

    -- ========================================================================
    -- SMOKE OF DECEIT AUTO-PURCHASE (pos 4 supports only)
    -- ========================================================================
    if _G.smoke_purchase_tracker == nil then _G.smoke_purchase_tracker = {} end
    if SUPPORT_HEROES[hero_name] and bot:GetAssignedLane() ~= 2 then
        local game_time = DotaTime()
        local last_smoke_time = _G.smoke_purchase_tracker[pid] or -9999
        if game_time > 600 then
            -- Check if bot already has smoke in inventory
            local has_smoke = false
            for slot = 0, 5 do
                local item = bot:GetItemInSlot(slot)
                if item and item:GetName() == "item_smoke_of_deceit" then
                    has_smoke = true
                    break
                end
            end
            if not has_smoke and bot:GetGold() >= 50 and (game_time - last_smoke_time) >= 300 then
                -- Check team smoke count (don't buy if team already has 3+)
                local team_smokes = 0
                local my_team = GetTeam()
                local ally_ids = GetTeamPlayers(my_team)
                for _, aid in ipairs(ally_ids) do
                    local ally = GetTeamMember(aid)
                    if ally ~= nil then
                        for slot = 0, 5 do
                            local item = ally:GetItemInSlot(slot)
                            if item and item:GetName() == "item_smoke_of_deceit" then
                                team_smokes = team_smokes + 1
                            end
                        end
                    end
                end
                if team_smokes < 3 then
                    bot:ActionImmediate_PurchaseItem("item_smoke_of_deceit")
                    _G.smoke_purchase_tracker[pid] = game_time
                    print(string.format("[SMOKE] ID:%d | %s bought Smoke of Deceit! TeamSmokes:%d | Gold:%d | GameTime:%.0f",
                        pid, hero_name, team_smokes, bot:GetGold(), game_time))
                end
            end
        end
    end

    -- ========================================================================
    -- WARD SENTRY AUTO-PURCHASE (supports vs invis heroes)
    -- ========================================================================
    if _G.sentry_purchase_tracker == nil then _G.sentry_purchase_tracker = {} end
    if SUPPORT_HEROES[hero_name] then
        local game_time = DotaTime()
        local last_sentry_time = _G.sentry_purchase_tracker[pid] or -9999
        if game_time > 240 then
            -- Check if enemy team has invisible heroes
            local enemy_has_invis = false
            local invis_hero_name = ""
            local enemy_team = GetOpposingTeam()
            local enemy_ids = GetTeamPlayers(enemy_team)
            for _, eid in ipairs(enemy_ids) do
                local ename = GetSelectedHeroName(eid)
                if ename and INVIS_HEROES[ename] then
                    enemy_has_invis = true
                    invis_hero_name = ename
                    break
                end
            end
            if enemy_has_invis then
                -- Check if bot already has sentry in inventory
                local has_sentry = false
                for slot = 0, 5 do
                    local item = bot:GetItemInSlot(slot)
                    if item and item:GetName() == "item_ward_sentry" then
                        has_sentry = true
                        break
                    end
                end
                local gold = bot:GetGold()
                local sentry_cd_ok = (game_time - last_sentry_time) >= 180
                if not has_sentry and gold >= 50 and sentry_cd_ok then
                    bot:ActionImmediate_PurchaseItem("item_ward_sentry")
                    _G.sentry_purchase_tracker[pid] = game_time
                    print(string.format("[SENTRY] ID:%d | %s bought Sentry Ward! Reason: enemy invis hero %s | Gold:%d | GameTime:%.0f",
                        pid, hero_name, invis_hero_name, gold, game_time))
                end
            end
        end
    end

    -- ========================================================================
    -- DUST OF APPEARANCE AUTO-PURCHASE (pos 4/5 supports vs invis heroes)
    -- ========================================================================
    if _G.dust_purchase_tracker == nil then _G.dust_purchase_tracker = {} end
    if SUPPORT_HEROES[hero_name] then
        local game_time = DotaTime()
        local last_dust_time = _G.dust_purchase_tracker[pid] or -9999
        -- Check if enemy team has invisible heroes
        local enemy_has_invis = false
        local enemy_team = GetOpposingTeam()
        local enemy_ids = GetTeamPlayers(enemy_team)
        for _, eid in ipairs(enemy_ids) do
            local ename = GetSelectedHeroName(eid)
            if ename and INVIS_HEROES[ename] then
                enemy_has_invis = true
                break
            end
        end
        if enemy_has_invis then
            -- Check if bot already has dust in inventory
            local has_dust = false
            for slot = 0, 5 do
                local item = bot:GetItemInSlot(slot)
                if item and item:GetName() == "item_dust" then
                    has_dust = true
                    break
                end
            end
            local gold = bot:GetGold()
            local dust_cd_ok = (game_time - last_dust_time) >= 240
            if not has_dust and gold >= 80 and dust_cd_ok then
                bot:ActionImmediate_PurchaseItem("item_dust")
                _G.dust_purchase_tracker[pid] = game_time
                print(string.format("[DUST] ID:%d | %s bought Dust of Appearance! Gold:%d | GameTime:%.0f",
                    pid, hero_name, gold, game_time))
            end
        end
    end

    local idx = purchase_index[pid] or 1
    
    -- END-GAME LUXURY PURCHASES & CONSUMABLES
    if idx > #bot.purchase_queue then
        -- Normal build completed! Add luxury items in real-time
        if bot.luxury_queued == nil then
            bot.luxury_queued = true
            
            -- Swift, Overwhelming, or Arcane Blink upgrade
            local blink_slot = bot:FindItemSlot("item_blink")
            if blink_slot ~= nil then
                local upgrade = "item_overwhelming_blink"
                if AGI_HEROES[hero_name] then upgrade = "item_swift_blink"
                elseif INT_HEROES[hero_name] then upgrade = "item_arcane_blink" end
                table.insert(bot.purchase_queue, upgrade)
                print(string.format("[BOT_PURCHASE] ID:%d | Core %s queued premium Blink upgrade: %s!", pid, hero_name, upgrade))
            end
            
            -- Moon Shard (buy and consume!)
            table.insert(bot.purchase_queue, "item_moon_shard")
            
            -- Level 2 Travel Boots
            table.insert(bot.purchase_queue, "item_travel_boots_2")
        else
            -- If we are at the end, check if we have moon shard and consume it!
            local moon_shard = bot:FindItemSlot("item_moon_shard")
            if moon_shard ~= nil and moon_shard >= 0 and moon_shard <= 5 then
                local shard = bot:GetItemInSlot(moon_shard)
                if shard and shard:IsFullyCastable() then
                    bot:Action_UseAbilityOnEntity(shard, bot)
                    print(string.format("[BOT_PURCHASE] ID:%d | %s consumed Moon Shard!", pid, hero_name))
                end
            end
            return
        end
    end

    local next_item = bot.purchase_queue[idx]
    
    -- SLOT MANAGEMENT (Selling starting items to free up slots)
    local empty_slots = 0
    for slot = 0, 5 do
        if bot:GetItemInSlot(slot) == nil then
            empty_slots = empty_slots + 1
        end
    end
    
    if empty_slots == 0 then
        -- Inventory is full! If we want to buy a new item or component, sell a starting item first
        local sell_slot = FindItemSlotToSell(bot)
        if sell_slot ~= -1 then
            local item_to_sell = bot:GetItemInSlot(sell_slot)
            if item_to_sell then
                bot:ActionImmediate_SellItem(item_to_sell)
                print(string.format("[BOT_PURCHASE] ID:%d | %s sold %s to free up inventory slot!", pid, hero_name, item_to_sell:GetName()))
            end
        end
    end
    
    -- Handle Secret Shop navigation
    if IsItemPurchasedFromSecretShop(next_item) and not bot:IsSecretShopVisible() then
        if bot:GetGold() >= GetItemCost(next_item) then
            local team = GetTeam()
            local secret_shop_loc = (team == 2) and Vector(-4800, 4800, 256) or Vector(4800, -4800, 256)
            bot:Action_MoveToLocation(secret_shop_loc)
            return
        end
    end

    local cost = GetItemCost(next_item)
    local gold = bot:GetGold()
    local game_time = DotaTime()
    
    -- [20/22] DYNAMIC COMPONENT BUYER (Закуп перед смертью)
    local raw_hp = bot:GetHealth()
    local max_hp = bot:GetMaxHealth()
    if raw_hp / math.max(max_hp, 1) < 0.15 and bot:WasRecentlyDamagedByAnyHero(2.0) then
        if gold >= cost then
            bot:ActionImmediate_PurchaseItem(next_item)
            purchase_index[pid] = idx + 1
            print(string.format("[EMERGENCY_BUY] ID:%d | %s aggressively bought %s before dying!", pid, hero_name, next_item))
            return
        end
    end

    -- [18/22] BUYBACK LUXURY INSURANCE (Резервирование на байбек)
    local is_support = SUPPORT_HEROES[hero_name] == true
    local reserve_for_buyback = false
    if game_time > 1500 and not is_support then -- Коры после 25 минут копят на выкуп
        local bb_cost = bot:GetBuybackCost()
        if (gold - cost) < bb_cost and bot:GetBuybackCooldown() <= 0 then
            reserve_for_buyback = true
        end
    end

    if gold >= cost then
        if reserve_for_buyback then
            if _G.last_buyback_ins_msg == nil then _G.last_buyback_ins_msg = {} end
            if game_time - (_G.last_buyback_ins_msg[pid] or 0) > 60 then
                _G.last_buyback_ins_msg[pid] = game_time
                print(string.format("[INSURANCE] ID:%d | Core %s SAVING gold for buyback! Blocked purchase of %s (cost %d, gold %d, bb_cost %d)", 
                    pid, hero_name, next_item, cost, gold, bot:GetBuybackCost()))
            end
        else
            bot:ActionImmediate_PurchaseItem(next_item)
            purchase_index[pid] = idx + 1
        end
    end
end
"""

    with open(OUTPUT_LUA_PATH, "w", encoding="utf-8") as f:
        f.write(lua_content)
    print(f"\nSuccessfully generated quad-build dynamic item purchase script at: {OUTPUT_LUA_PATH}")

    # Copy to Dota 2 bots directory
    if os.path.exists(DOTA_VSCRIPTS_BOTS_DIR):
        dst_path = os.path.join(DOTA_VSCRIPTS_BOTS_DIR, "item_purchase_generic.lua")
        try:
            shutil.copy2(OUTPUT_LUA_PATH, dst_path)
            print(f"Successfully deployed dynamic item builds directly to Dota 2 client: {dst_path}")
        except Exception as e:
            print(f"Error deploying item purchase script: {e}")

if __name__ == "__main__":
    main()
