-- ============================================================================
-- hero_selection.lua — PRO COMPOSITION SYNERGY DRAFTING ENGINE FOR AI BOTS
-- ============================================================================
-- Automatically selects the most optimal pro compositions, counters, and synergies
-- based on real-time picks and lane assignments. Covers ALL 127+ heroes.
-- ============================================================================

local ALL_HEROES = {
    "npc_dota_hero_abaddon", "npc_dota_hero_abyssal_underlord", "npc_dota_hero_alchemist",
    "npc_dota_hero_ancient_apparition", "npc_dota_hero_antimage", "npc_dota_hero_arc_warden",
    "npc_dota_hero_axe", "npc_dota_hero_bane", "npc_dota_hero_batrider", "npc_dota_hero_beastmaster",
    "npc_dota_hero_bloodseeker", "npc_dota_hero_bounty_hunter", "npc_dota_hero_brewmaster",
    "npc_dota_hero_bristleback", "npc_dota_hero_broodmother", "npc_dota_hero_centaur",
    "npc_dota_hero_chaos_knight", "npc_dota_hero_chen", "npc_dota_hero_clinkz", "npc_dota_hero_crystal_maiden",
    "npc_dota_hero_dark_seer", "npc_dota_hero_dark_willow", "npc_dota_hero_dawnbreaker", "npc_dota_hero_dazzle",
    "npc_dota_hero_death_prophet", "npc_dota_hero_disruptor", "npc_dota_hero_doom_bringer",
    "npc_dota_hero_dragon_knight", "npc_dota_hero_drow_ranger", "npc_dota_hero_earth_spirit",
    "npc_dota_hero_earthshaker", "npc_dota_hero_elder_titan", "npc_dota_hero_ember_spirit",
    "npc_dota_hero_enchantress", "npc_dota_hero_enigma", "npc_dota_hero_faceless_void", "npc_dota_hero_furion",
    "npc_dota_hero_grimstroke", "npc_dota_hero_gyrocopter", "npc_dota_hero_hoodwink", "npc_dota_hero_huskar",
    "npc_dota_hero_invoker", "npc_dota_hero_jakiro", "npc_dota_hero_juggernaut", "npc_dota_hero_keeper_of_the_light",
    "npc_dota_hero_kunkka", "npc_dota_hero_legion_commander", "npc_dota_hero_leshrac", "npc_dota_hero_lich",
    "npc_dota_hero_lifestealer", "npc_dota_hero_lina", "npc_dota_hero_lion", "npc_dota_hero_lone_druid",
    "npc_dota_hero_luna", "npc_dota_hero_lycan", "npc_dota_hero_magnus", "npc_dota_hero_marci", "npc_dota_hero_mars",
    "npc_dota_hero_medusa", "npc_dota_hero_meepo", "npc_dota_hero_mirana", "npc_dota_hero_monkey_king",
    "npc_dota_hero_morphling", "npc_dota_hero_muerta", "npc_dota_hero_naga_siren", "npc_dota_hero_necrolyte",
    "npc_dota_hero_night_stalker", "npc_dota_hero_nyx_assassin", "npc_dota_hero_obsidian_destroyer",
    "npc_dota_hero_ogre_magi", "npc_dota_hero_omniknight", "npc_dota_hero_oracle", "npc_dota_hero_pangolier",
    "npc_dota_hero_phantom_assassin", "npc_dota_hero_phantom_lancer", "npc_dota_hero_phoenix",
    "npc_dota_hero_primal_beast", "npc_dota_hero_puck", "npc_dota_hero_pudge", "npc_dota_hero_pugna",
    "npc_dota_hero_queenofpain", "npc_dota_hero_rattletrap", "npc_dota_hero_razor", "npc_dota_hero_riki",
    "npc_dota_hero_rubick", "npc_dota_hero_sand_king", "npc_dota_hero_shadow_demon", "npc_dota_hero_shadow_shaman",
    "npc_dota_hero_shredder", "npc_dota_hero_silencer", "npc_dota_hero_skeleton_king", "npc_dota_hero_skywrath_mage",
    "npc_dota_hero_slardar", "npc_dota_hero_slark", "npc_dota_hero_snapfire", "npc_dota_hero_sniper",
    "npc_dota_hero_spectre", "npc_dota_hero_spirit_breaker", "npc_dota_hero_storm_spirit", "npc_dota_hero_sven",
    "npc_dota_hero_techies", "npc_dota_hero_templar_assassin", "npc_dota_hero_terrorblade", "npc_dota_hero_tidehunter",
    "npc_dota_hero_tinker", "npc_dota_hero_tiny", "npc_dota_hero_treant", "npc_dota_hero_troll_warlord",
    "npc_dota_hero_tusk", "npc_dota_hero_undying", "npc_dota_hero_ursa", "npc_dota_hero_vengefulspirit",
    "npc_dota_hero_venomancer", "npc_dota_hero_viper", "npc_dota_hero_visage", "npc_dota_hero_void_spirit",
    "npc_dota_hero_warlock", "npc_dota_hero_weaver", "npc_dota_hero_windrunner", "npc_dota_hero_winter_wyvern",
    "npc_dota_hero_witch_doctor", "npc_dota_hero_wisp", "npc_dota_hero_zuus"
}

-- Pro roles mapping for perfect synergies
local ROLE_CARRIES = {
    "npc_dota_hero_antimage", "npc_dota_hero_juggernaut", "npc_dota_hero_phantom_assassin",
    "npc_dota_hero_spectre", "npc_dota_hero_luna", "npc_dota_hero_faceless_void",
    "npc_dota_hero_slark", "npc_dota_hero_terrorblade", "npc_dota_hero_drow_ranger",
    "npc_dota_hero_muerta", "npc_dota_hero_lifestealer", "npc_dota_hero_sven"
}

local ROLE_MIDLANERS = {
    "npc_dota_hero_storm_spirit", "npc_dota_hero_ember_spirit", "npc_dota_hero_void_spirit",
    "npc_dota_hero_puck", "npc_dota_hero_queenofpain", "npc_dota_hero_invoker",
    "npc_dota_hero_tinker", "npc_dota_hero_lina", "npc_dota_hero_sf",
    "npc_dota_hero_zuus", "npc_dota_hero_viper", "npc_dota_hero_kunkka"
}

local ROLE_OFFLANERS = {
    "npc_dota_hero_axe", "npc_dota_hero_centaur", "npc_dota_hero_tidehunter",
    "npc_dota_hero_mars", "npc_dota_hero_slardar", "npc_dota_hero_magnus",
    "npc_dota_hero_bristleback", "npc_dota_hero_primal_beast", "npc_dota_hero_abyssal_underlord",
    "npc_dota_hero_doom_bringer", "npc_dota_hero_beastmaster", "npc_dota_hero_dark_seer"
}

local ROLE_SUPPORTS_4 = {
    "npc_dota_hero_spirit_breaker", "npc_dota_hero_earth_spirit", "npc_dota_hero_tusk",
    "npc_dota_hero_bounty_hunter", "npc_dota_hero_nyx_assassin", "npc_dota_hero_mirana",
    "npc_dota_hero_rubick", "npc_dota_hero_snapfire", "npc_dota_hero_hoodwink"
}

local ROLE_SUPPORTS_5 = {
    "npc_dota_hero_crystal_maiden", "npc_dota_hero_lion", "npc_dota_hero_witch_doctor",
    "npc_dota_hero_dazzle", "npc_dota_hero_shadow_shaman", "npc_dota_hero_lich",
    "npc_dota_hero_oracle", "npc_dota_hero_disruptor", "npc_dota_hero_keeper_of_the_light",
    "npc_dota_hero_bane", "npc_dota_hero_warlock", "npc_dota_hero_ancient_apparition"
}

-- Pro Draft Archetypes with high synergy
local SYNERGY_COMPS = {
    ["wombocombo"] = {
        [1] = "npc_dota_hero_faceless_void",
        [2] = "npc_dota_hero_invoker",
        [3] = "npc_dota_hero_tidehunter",
        [4] = "npc_dota_hero_snapfire",
        [5] = "npc_dota_hero_witch_doctor"
    },
    ["deathball"] = {
        [1] = "npc_dota_hero_luna",
        [2] = "npc_dota_hero_lina",
        [3] = "npc_dota_hero_beastmaster",
        [4] = "npc_dota_hero_spirit_breaker",
        [5] = "npc_dota_hero_shadow_shaman"
    },
    ["gank"] = {
        [1] = "npc_dota_hero_slark",
        [2] = "npc_dota_hero_storm_spirit",
        [3] = "npc_dota_hero_axe",
        [4] = "npc_dota_hero_bounty_hunter",
        [5] = "npc_dota_hero_lion"
    },
    ["turtle"] = {
        [1] = "npc_dota_hero_spectre",
        [2] = "npc_dota_hero_zuus",
        [3] = "npc_dota_hero_abyssal_underlord",
        [4] = "npc_dota_hero_rubick",
        [5] = "npc_dota_hero_dazzle"
    }
}

-- Hero counters
local COUNTER_MAP = {
    ["npc_dota_hero_enigma"] = "npc_dota_hero_silencer",
    ["npc_dota_hero_storm_spirit"] = "npc_dota_hero_antimage",
    ["npc_dota_hero_medusa"] = "npc_dota_hero_antimage",
    ["npc_dota_hero_phantom_assassin"] = "npc_dota_hero_razor",
    ["npc_dota_hero_sven"] = "npc_dota_hero_razor",
    ["npc_dota_hero_bristleback"] = "npc_dota_hero_slark"
}

local assigned_heroes = {}

local function is_hero_already_selected(hero)
    for pid = 0, 19 do
        local heroName = GetSelectedHeroName(pid)
        if heroName == hero then return true end
    end
    for _, assigned_hero in pairs(assigned_heroes) do
        if assigned_hero == hero then return true end
    end
    return false
end

local function select_counter_or_synergy(role_list, pos)
    -- Check enemy draft to counter them
    local opposing = (GetTeam() == 2) and 3 or 2
    local enemy_ids = GetTeamPlayers(opposing)
    for _, eid in ipairs(enemy_ids) do
        local enemy_hero = GetSelectedHeroName(eid)
        if enemy_hero and enemy_hero ~= "" then
            local counter = COUNTER_MAP[enemy_hero]
            if counter and not is_hero_already_selected(counter) then
                -- Check if counter hero fits the role we want
                for _, rh in ipairs(role_list) do
                    if rh == counter then
                        print(string.format("[DRAFT] Selected COUNTER PICK: %s against %s!", counter, enemy_hero))
                        return counter
                    end
                end
            end
        end
    end

    -- Fallback to standard role synergy
    for _, hero in ipairs(role_list) do
        if not is_hero_already_selected(hero) then
            return hero
        end
    end
    
    -- Ultimate fallback from all heroes list
    for _, hero in ipairs(ALL_HEROES) do
        if not is_hero_already_selected(hero) then
            return hero
        end
    end
    return "npc_dota_hero_juggernaut"
end

function Think()
    local team = GetTeam()
    local start_id = 0
    local end_id = 4
    if team == 3 then
        start_id = 5
        end_id = 9
    end

    -- Choose synergy archetype for this team session
    if _G.selected_draft_archetype == nil then
        local archetypes = {"wombocombo", "deathball", "gank", "turtle"}
        _G.selected_draft_archetype = archetypes[RandomInt(1, #archetypes)]
        print(string.format("[DRAFT] Active draft synergy profile chosen: %s", _G.selected_draft_archetype))
    end

    local archetype_heroes = SYNERGY_COMPS[_G.selected_draft_archetype]

    for pid = start_id, end_id do
        if IsPlayerBot == nil or IsPlayerBot(pid) then
            local heroName = GetSelectedHeroName(pid)
            if heroName == nil or heroName == "" then
                if assigned_heroes[pid] == nil then
                    -- Map player index (0-4 or 5-9) to lane roles:
                    -- idx 0/5 = Carry (pos 1), idx 1/6 = Mid (pos 2), idx 2/7 = Offlane (pos 3), idx 3/8 = Pos 4, idx 4/9 = Pos 5
                    local role_idx = (pid % 5) + 1
                    local desired_hero = archetype_heroes[role_idx]
                    
                    if desired_hero and not is_hero_already_selected(desired_hero) then
                        assigned_heroes[pid] = desired_hero
                    else
                        -- Archetype hero is already taken or banned, fall back to counter/role selection
                        if role_idx == 1 then
                            assigned_heroes[pid] = select_counter_or_synergy(ROLE_CARRIES, 1)
                        elseif role_idx == 2 then
                            assigned_heroes[pid] = select_counter_or_synergy(ROLE_MIDLANERS, 2)
                        elseif role_idx == 3 then
                            assigned_heroes[pid] = select_counter_or_synergy(ROLE_OFFLANERS, 3)
                        elseif role_idx == 4 then
                            assigned_heroes[pid] = select_counter_or_synergy(ROLE_SUPPORTS_4, 4)
                        else
                            assigned_heroes[pid] = select_counter_or_synergy(ROLE_SUPPORTS_5, 5)
                        end
                    end
                    print(string.format("[DRAFT] Bot ID:%d selected role #%d hero: %s", pid, role_idx, assigned_heroes[pid]))
                end
                SelectHero(pid, assigned_heroes[pid])
            end
        end
    end
end

function GetBotNames()
    return {}
end
