"""
export_model_to_lua.py
Exports trained HistGradientBoosting models (X and Y) for Positions 1-5 into pure Lua code.
Also embeds advanced macro strategy and micro-mechanical overlays directly into bot_generic.lua Think loop.
"""

import joblib
import os

MODEL_DIR = r"C:\бот\model"
OUTPUT_PATH = r"C:\бот\bot_generic.lua"

FEATURE_NAMES = [
    'hero_hp_pct', 'hero_mana_pct',
    'creep_1_dx', 'creep_1_dy', 'creep_1_hp_pct', 'creep_1_dist', 'creep_1_team',
    'creep_2_dx', 'creep_2_dy', 'creep_2_hp_pct', 'creep_2_dist', 'creep_2_team',
    'creep_3_dx', 'creep_3_dy', 'creep_3_hp_pct', 'creep_3_dist', 'creep_3_team',
    'creep_4_dx', 'creep_4_dy', 'creep_4_hp_pct', 'creep_4_dist', 'creep_4_team',
    'creep_5_dx', 'creep_5_dy', 'creep_5_hp_pct', 'creep_5_dist', 'creep_5_team',
]

LUA_FEATURE_MAP = {
    0: 'hp', 1: 'mp',
    2: 'c1x', 3: 'c1y', 4: 'c1h', 5: 'c1d', 6: 'c1t',
    7: 'c2x', 8: 'c2y', 9: 'c2h', 10: 'c2d', 11: 'c2t',
    12: 'c3x', 13: 'c3y', 14: 'c3h', 15: 'c3d', 16: 'c3t',
    17: 'c4x', 18: 'c4y', 19: 'c4h', 20: 'c4d', 21: 'c4t',
    22: 'c5x', 23: 'c5y', 24: 'c5h', 25: 'c5d', 26: 'c5t',
}

def export_tree_to_lua(tree_predictor, indent_level=1):
    nodes = tree_predictor.nodes
    lines = []
    
    def recurse(node_idx, indent):
        node = nodes[node_idx]
        prefix = "    " * indent
        
        is_leaf = node['is_leaf']
        if is_leaf:
            value = float(node['value'])
            lines.append(f"{prefix}return {value:.6f}")
        else:
            feature_idx = int(node['feature_idx'])
            threshold = float(node['num_threshold'])
            left = int(node['left'])
            right = int(node['right'])
            
            feat_name = LUA_FEATURE_MAP.get(feature_idx, f'f[{feature_idx}]')
            lines.append(f"{prefix}if {feat_name} <= {threshold:.6f} then")
            recurse(left, indent + 1)
            lines.append(f"{prefix}else")
            recurse(right, indent + 1)
            lines.append(f"{prefix}end")
    
    recurse(0, indent_level)
    return "\n".join(lines)

def export_model_to_lua_functions(model, func_prefix):
    lines = []
    predictors = model._predictors
    baseline = float(model._baseline_prediction)
    learning_rate = float(model.learning_rate)
    
    n_trees = len(predictors)
    print(f"  Exporting {n_trees} trees for {func_prefix}...")
    
    for i, tree_list in enumerate(predictors):
        tree = tree_list[0]
        lines.append(f"function {func_prefix}_t{i}(hp,mp,c1x,c1y,c1h,c1d,c1t,c2x,c2y,c2h,c2d,c2t,c3x,c3y,c3h,c3d,c3t,c4x,c4y,c4h,c4d,c4t,c5x,c5y,c5h,c5d,c5t)")
        lines.append(export_tree_to_lua(tree, indent_level=1))
        lines.append("end")
        lines.append("")
    
    lines.append(f"function predict_{func_prefix}(hp,mp,c1x,c1y,c1h,c1d,c1t,c2x,c2y,c2h,c2d,c2t,c3x,c3y,c3h,c3d,c3t,c4x,c4y,c4h,c4d,c4t,c5x,c5y,c5h,c5d,c5t)")
    lines.append(f"    local s = {baseline:.6f}")
    
    for i in range(n_trees):
        lines.append(f"    s = s + {func_prefix}_t{i}(hp,mp,c1x,c1y,c1h,c1d,c1t,c2x,c2y,c2h,c2d,c2t,c3x,c3y,c3h,c3d,c3t,c4x,c4y,c4h,c4d,c4t,c5x,c5y,c5h,c5d,c5t)")
    
    lines.append("    return s")
    lines.append("end")
    lines.append("")
    
    return "\n".join(lines), n_trees

def main():
    print("=== Exporting Position-Specific Models to Pure Lua ===")
    
    lua_parts = []
    
    # Header
    lua_parts.append("""-- ============================================================================
-- Dota 2 AI Imitation Learning Bot (bot_generic.lua)
-- ============================================================================
-- FULLY SELF-CONTAINED: trained models for Positions 1-5 embedded directly.
-- No external Python server needed! Trained on pro top MMR professional matches.
-- ============================================================================
""")
    
    total_trees = 0
    
    for pos in range(1, 6):
        print(f"\nProcessing Position {pos} Models...")
        model_x_path = os.path.join(MODEL_DIR, f"dota_ai_model_x_pos{pos}.joblib")
        model_y_path = os.path.join(MODEL_DIR, f"dota_ai_model_y_pos{pos}.joblib")
        
        if not os.path.exists(model_x_path) or not os.path.exists(model_y_path):
            print(f"  Position {pos} models not found. Bootstrapping with standard models as fallback.")
            model_x_path = os.path.join(MODEL_DIR, "dota_ai_model_x.joblib")
            model_y_path = os.path.join(MODEL_DIR, "dota_ai_model_y.joblib")
            
        if os.path.exists(model_x_path) and os.path.exists(model_y_path):
            model_x = joblib.load(model_x_path)
            model_y = joblib.load(model_y_path)
            
            lua_x, nx = export_model_to_lua_functions(model_x, f"mx_pos{pos}")
            lua_y, ny = export_model_to_lua_functions(model_y, f"my_pos{pos}")
            
            total_trees += (nx + ny)
            
            lua_parts.append(f"-- ============ POSITION {pos} ML MODEL ============")
            lua_parts.append(lua_x)
            lua_parts.append(lua_y)

    # Add support hero definitions and position mapping helper
    lua_parts.append("""
-- ============ STRATEGY AND ASYMMETRY SETUP ============
local SUPPORT_HEROES = {
    ["npc_dota_hero_crystal_maiden"] = true,
    ["npc_dota_hero_lion"] = true,
    ["npc_dota_hero_witch_doctor"] = true,
    ["npc_dota_hero_dazzle"] = true,
    ["npc_dota_hero_shadow_shaman"] = true,
    ["npc_dota_hero_lich"] = true,
    ["npc_dota_hero_oracle"] = true,
    ["npc_dota_hero_disruptor"] = true,
    ["npc_dota_hero_keeper_of_the_light"] = true,
    ["npc_dota_hero_bane"] = true,
    ["npc_dota_hero_warlock"] = true,
    ["npc_dota_hero_ancient_apparition"] = true,
    ["npc_dota_hero_grimstroke"] = true,
    ["npc_dota_hero_jakiro"] = true,
    ["npc_dota_hero_skywrath_mage"] = true,
    ["npc_dota_hero_treant"] = true,
    ["npc_dota_hero_undying"] = true,
    ["npc_dota_hero_rubick"] = true,
    ["npc_dota_hero_chen"] = true,
    ["npc_dota_hero_wisp"] = true,
    ["npc_dota_hero_shadow_demon"] = true,
    ["npc_dota_hero_snapfire"] = true,
    ["npc_dota_hero_mirana"] = true,
    ["npc_dota_hero_bounty_hunter"] = true,
    ["npc_dota_hero_nyx_assassin"] = true,
    ["npc_dota_hero_spirit_breaker"] = true,
    ["npc_dota_hero_earth_spirit"] = true,
    ["npc_dota_hero_tusk"] = true,
    ["npc_dota_hero_elder_titan"] = true,
    ["npc_dota_hero_techies"] = true,
    ["npc_dota_hero_hoodwink"] = true,
}

local function GetBotPosition(bot)
    local team = GetTeam()
    local lane = bot:GetAssignedLane()
    local hero = bot:GetUnitName()
    local is_support = SUPPORT_HEROES[hero] == true
    
    if lane == 2 then -- LANE_MID
        return 2 -- Position 2: Midlaner
    end
    
    if team == 2 then -- Radiant
        if lane == 3 then -- LANE_BOT (Safe Lane)
            return is_support and 5 or 1 -- Pos 5 or Pos 1
        elseif lane == 1 then -- LANE_TOP (Offlane)
            return is_support and 4 or 3 -- Pos 4 or Pos 3
        end
    else -- Dire
        if lane == 1 then -- LANE_TOP (Safe Lane)
            return is_support and 5 or 1 -- Pos 5 or Pos 1
        elseif lane == 3 then -- LANE_BOT (Offlane)
            return is_support and 4 or 3 -- Pos 4 or Pos 3
        end
    end
    
    return 1 -- Fallback default
end

-- Helper to calculate distance 2D safely
local function GetDistance(v1, v2)
    if v1 == nil or v2 == nil then return 999999 end
    return math.sqrt((v1.x - v2.x)^2 + (v1.y - v2.y)^2)
end

-- Pro Ward Spots from ward_spots.json
local WARD_SPOTS = {
    -- Defensive Radiant
    {x = -1700, y = -4200, z = 128, desc = "Rad Jungle Deep Edge", side = "radiant_defensive"},
    {x = -3200, y = -3800, z = 128, desc = "Rad Jungle High Ground Ramp", side = "radiant_defensive"},
    {x = 3500, y = -6200, z = 128, desc = "Rad Bottom T2 Jungle", side = "radiant_defensive"},
    {x = 4800, y = -3800, z = 128, desc = "Rad Safe T1 Behind Trees", side = "radiant_defensive"},
    {x = -6100, y = -1500, z = 128, desc = "Rad Secret Shop Cliff", side = "radiant_defensive"},
    
    -- Defensive Dire
    {x = 1700, y = 4200, z = 128, desc = "Dire Jungle Deep Edge", side = "dire_defensive"},
    {x = 3200, y = 3800, z = 128, desc = "Dire Jungle High Ground Ramp", side = "dire_defensive"},
    {x = -3500, y = 6200, z = 128, desc = "Dire Top T2 Jungle", side = "dire_defensive"},
    {x = -4800, y = 3800, z = 128, desc = "Dire Safe T1 Behind Trees", side = "dire_defensive"},
    {x = 6100, y = 1500, z = 128, desc = "Dire Secret Shop Cliff", side = "dire_defensive"},
}

-- Jungle Camp Vectors for Stacking
local JUNGLE_CAMPS = {
    [2] = { -- Radiant (Team 2)
        {x = -3600, y = -4500, z = 128},
        {x = -1600, y = -3500, z = 128},
        {x = -200, y = -3200, z = 128}
    },
    [3] = { -- Dire (Team 3)
        {x = 3600, y = 4500, z = 128},
        {x = 1600, y = 3500, z = 128},
        {x = 200, y = 3200, z = 128}
    }
}

-- Pull Camps for Safe Lane pull (Отводы) at XX:15 / XX:45
local PULL_CAMPS = {
    [2] = { -- Radiant Small Camp
        camp = Vector(3050, -4500, 256),
        pull_loc = Vector(3200, -5400, 256)
    },
    [3] = { -- Dire Small Camp
        camp = Vector(-3050, 4500, 256),
        pull_loc = Vector(-3200, 5400, 256)
    }
}

-- Smart Courier Delivery Utility
local function ManageCourierDelivery(bot)
    local now = GameTime()
    local bot_id = bot:GetPlayerID()
    if _G.last_courier_check == nil then _G.last_courier_check = {} end
    local last_check = _G.last_courier_check[bot_id] or 0
    if now - last_check < 8.0 then return end
    _G.last_courier_check[bot_id] = now
    
    local num_in_stash = bot:GetNumItemsInStash()
    if num_in_stash > 0 then
        local courier = GetCourier(bot_id % 5)
        if courier ~= nil and courier:IsAlive() then
            local state = GetCourierState(courier)
            if state == COURIER_STATE_AT_BASE or state == COURIER_STATE_IDLE then
                bot:ActionImmediate_Courier(courier, COURIER_ACTION_TRANSFER_ITEMS)
                print(string.format("[BOT_UTILITY] Sent Courier for ID:%d with %d items!", bot_id, num_in_stash))
            end
        end
    end
end

-- Dynamic support warding cliff spot selector
local function SelectWardSpot(bot, team)
    local candidates = {}
    local side_tag = (team == 2) and "radiant_defensive" or "dire_defensive"
    for _, spot in ipairs(WARD_SPOTS) do
        if spot.side == side_tag then
            table.insert(candidates, spot)
        end
    end
    local idx = (bot:GetPlayerID() % #candidates) + 1
    return candidates[idx]
end

local function get_nearest_creeps(bot)
    local nearby = {}
    local enemy_creeps = bot:GetNearbyCreeps(1600, true)
    if enemy_creeps then
        for _, creep in ipairs(enemy_creeps) do
            if creep and creep:IsAlive() then table.insert(nearby, creep) end
        end
    end
    local ally_creeps = bot:GetNearbyCreeps(1600, false)
    if ally_creeps then
        for _, creep in ipairs(ally_creeps) do
            if creep and creep:IsAlive() then table.insert(nearby, creep) end
        end
    end
    table.sort(nearby, function(a, b)
        return GetUnitToUnitDistance(bot, a) < GetUnitToUnitDistance(bot, b)
    end)
    local result = {}
    for i = 1, 5 do
        if nearby[i] then table.insert(result, nearby[i]) end
    end
    return result
end

-- Global tables for tracking state
local last_think_time = {}
local warding_cooldown = {}
local warding_state = {}
local current_jungle_camp = {}

-- ============ BOT THINK LOGIC ============
local THINK_INTERVAL = 0.4

function Think()
    local bot = GetBot()
    if bot == nil or not bot:IsAlive() or bot:IsIllusion() then
        return
    end

    local bot_id = bot:GetPlayerID()
    local team = GetTeam()
    local now = GameTime()
    local prev = last_think_time[bot_id] or 0

    if (now - prev) < THINK_INTERVAL then return end
    last_think_time[bot_id] = now

    local bot_loc = bot:GetLocation()
    local pos = GetBotPosition(bot)

    -- ==================== [46/22] BURMALDA CHAMPIONSHIP GREETING ====================
    if _G.burmalda_greeted == nil then _G.burmalda_greeted = {} end
    if not _G.burmalda_greeted[bot_id] and now > 2.0 and now < 60.0 then
        _G.burmalda_greeted[bot_id] = true
        bot:ActionImmediate_Chat("БУРМАЛДА", true)
        print(string.format("[BURMALDA] Bot ID:%d said BURMALDA at game start!", bot_id))
    end

    if _G.burmalda_respawn_deaths == nil then _G.burmalda_respawn_deaths = {} end
    local current_deaths = GetHeroDeaths(bot_id)
    local last_deaths = _G.burmalda_respawn_deaths[bot_id] or 0
    if current_deaths > last_deaths then
        _G.burmalda_respawn_deaths[bot_id] = current_deaths
        bot:ActionImmediate_Chat("БУРМАЛДА!", true)
        print(string.format("[BURMALDA] Bot ID:%d said BURMALDA upon respawning!", bot_id))
    end

    -- ==================== [39/22] DYNAMIC GLYPH OF FORTIFICATION (Умный Глиф) ====================
    if _G.glyph_cooldown == nil then _G.glyph_cooldown = 0 end
    if _G.glyph_activated_time == nil then _G.glyph_activated_time = 0 end
    
    local glyph_cd = GetGlyphCooldown()
    
    if glyph_cd == 0 and (now - _G.glyph_activated_time) > 40 then
        -- 1. СТРОГИЙ АНАЛИЗ ГЛАВНЫХ ЗДАНИЙ (Ancient, T3)
        local ancient = GetAncient(team)
        if ancient ~= nil and ancient:IsAlive() then
            local ancient_hp = ancient:GetHealth()
            local ancient_max = ancient:GetMaxHealth()
            local ancient_attackers = ancient:GetNearbyHeroes(1300, true, BOT_MODE_NONE)
            
            -- Если Трон под прямой атакой и здоровье ниже 90%
            if ancient_attackers ~= nil and #ancient_attackers >= 1 and (ancient_hp / ancient_max) < 0.90 then
                ActionImmediate_Glyph()
                _G.glyph_activated_time = now
                print(string.format("[DYNAMIC_GLYPH] CRITICAL TRIGGER! Popped Glyph of Fortification! Reason: ANCIENT under threat from %d enemies, HP: %.1f%%", #ancient_attackers, (ancient_hp/ancient_max)*100))
            end
        end
        
        -- 2. АНАЛИЗ Т3-ТОВАРОB И БАРАКОВ (Хайграунд)
        local t3_towers = {
            GetTower(team, TOWER_TOP_3),
            GetTower(team, TOWER_MID_3),
            GetTower(team, TOWER_BOT_3)
        }
        for _, t3 in ipairs(t3_towers) do
            if t3 ~= nil and t3:IsAlive() then
                local t3_hp = t3:GetHealth()
                local t3_max = t3:GetMaxHealth()
                local attackers = t3:GetNearbyHeroes(1300, true, BOT_MODE_NONE)
                if attackers ~= nil and #attackers >= 2 and (t3_hp / t3_max) < 0.80 then
                    ActionImmediate_Glyph()
                    _G.glyph_activated_time = now
                    print(string.format("[DYNAMIC_GLYPH] HIGH GROUND DEFENSE! Popped Glyph! Reason: T3 Tower under heavy attack from %d enemies, HP: %.1f%%", #attackers, (t3_hp/t3_max)*100))
                    break
                end
            end
        end
        
        local barracks_list = {
            GetBarracks(team, BARRACKS_TOP_MELEE), GetBarracks(team, BARRACKS_TOP_RANGED),
            GetBarracks(team, BARRACKS_MID_MELEE), GetBarracks(team, BARRACKS_MID_RANGED),
            GetBarracks(team, BARRACKS_BOT_MELEE), GetBarracks(team, BARRACKS_BOT_RANGED)
        }
        for _, rax in ipairs(barracks_list) do
            if rax ~= nil and rax:IsAlive() then
                local rax_hp = rax:GetHealth()
                local rax_max = rax:GetMaxHealth()
                local attackers = rax:GetNearbyHeroes(1300, true, BOT_MODE_NONE)
                if attackers ~= nil and #attackers >= 2 and (rax_hp / rax_max) < 0.85 then
                    ActionImmediate_Glyph()
                    _G.glyph_activated_time = now
                    print(string.format("[DYNAMIC_GLYPH] BARRACKS DEFENSE! Popped Glyph! Reason: Barracks %s under siege by %d enemies, HP: %.1f%%", rax:GetUnitName(), #attackers, (rax_hp/rax_max)*100))
                    break
                end
            end
        end
        
        -- 3. АНАЛИЗ Т1/Т2 ВЫШЕК (Сдерживание давления)
        if now > 300 and (now - _G.glyph_activated_time) > 40 then
            local outer_towers = {
                GetTower(team, TOWER_TOP_1), GetTower(team, TOWER_MID_1), GetTower(team, TOWER_BOT_1),
                GetTower(team, TOWER_TOP_2), GetTower(team, TOWER_MID_2), GetTower(team, TOWER_BOT_2)
            }
            for _, tower in ipairs(outer_towers) do
                if tower ~= nil and tower:IsAlive() then
                    local thp = tower:GetHealth()
                    local tmax = tower:GetMaxHealth()
                    local enemy_creeps = tower:GetNearbyCreeps(900, true)
                    
                    -- Если вышка падает под огромной пачкой крипов (5+), а союзников рядом нет для защиты
                    if enemy_creeps ~= nil and #enemy_creeps >= 5 and (thp / tmax) < 0.35 then
                        local nearby_allies = tower:GetNearbyHeroes(1200, false, BOT_MODE_NONE)
                        if nearby_allies == nil or #nearby_allies == 0 then
                            ActionImmediate_Glyph()
                            _G.glyph_activated_time = now
                            print(string.format("[DYNAMIC_GLYPH] DENIAL PREVENTION! Popped Glyph! Reason: Outer Tower %s is solo-sieged by %d creeps, HP: %.1f%%", tower:GetUnitName(), #enemy_creeps, (thp/tmax)*100))
                            break
                        end
                    end
                end
            end
        end
    end

    -- Auto-Courier Delivery
    ManageCourierDelivery(bot)

    local hp = 1.0
    if bot:GetMaxHealth() > 0 then hp = bot:GetHealth() / bot:GetMaxHealth() end
    local mp = 0.0
    if bot:GetMaxMana() > 0 then mp = bot:GetMana() / bot:GetMaxMana() end

    -- ==================== [1/22] TREAD SWITCHING MICRO ====================
    local treads = bot:FindItemSlot("item_power_treads")
    if treads ~= nil and treads >= 0 and treads <= 5 then
        local treads_item = bot:GetItemInSlot(treads)
        if treads_item ~= nil then
            if _G.treads_state == nil then _G.treads_state = {} end
            local current_state = _G.treads_state[bot_id] or 0 -- 0=STR, 1=INT, 2=AGI
            
            -- Определение идеального атрибута:
            local target_state = 0 -- По умолчанию STR (для выживаемости)
            if bot:IsCastingAbility() or (bot:GetMana() / math.max(bot:GetMaxMana(), 1)) < 0.3 then
                target_state = 1 -- INT перед кастом или при дефиците маны
            elseif bot:HasModifier("modifier_item_buff_treads") then
                -- Если восстанавливаем здоровье/ману с помощью расходников
                if bot:HasModifier("modifier_filler_healing") or bot:HasModifier("modifier_clarity") or bot:HasModifier("modifier_tango") then
                    target_state = 2 -- AGI для максимальной эффективности регена
                end
            end
            
            -- Переключаем Treads кликами
            if current_state ~= target_state then
                bot:ActionImmediate_UseAbility(treads_item)
                _G.treads_state[bot_id] = (current_state + 1) % 3
                print(string.format("[TREADS] ID:%d | Switching treads towards target %d (current %d)", bot_id, target_state, _G.treads_state[bot_id]))
            end
        end
    end

    -- ==================== [2/22] ARMLET TOGGLING MACRO ====================
    local armlet = bot:FindItemSlot("item_armlet")
    if armlet ~= nil and armlet >= 0 and armlet <= 5 then
        local armlet_item = bot:GetItemInSlot(armlet)
        if armlet_item ~= nil then
            local is_active = bot:HasModifier("modifier_item_armlet_unholy_strength")
            local raw_hp = bot:GetHealth()
            if raw_hp < 180 and is_active then
                -- Абуз Armlet: выключаем и мгновенно включаем
                bot:ActionImmediate_ToggleAbility(armlet_item)
                bot:ActionImmediate_ToggleAbility(armlet_item)
                print(string.format("[ARMLET] ID:%d | Perfect Armlet Toggle at %d HP!", bot_id, raw_hp))
            end
        end
    end

    -- ==================== [3/22] EVASION PROJECTILE DODGER ====================
    local nearby_enemies = bot:GetNearbyHeroes(1600, true, BOT_MODE_NONE)
    if nearby_enemies ~= nil and #nearby_enemies > 0 then
        -- Поиск предметов для доджа
        local manta = bot:FindItemSlot("item_manta")
        local blink = bot:FindItemSlot("item_blink")
        local eul = bot:FindItemSlot("item_cyclone")
        
        for _, enemy in ipairs(nearby_enemies) do
            if enemy ~= nil and enemy:IsCastingAbility() then
                -- Если враг кастует стан/нюк на нас
                if manta ~= nil and manta >= 0 and manta <= 5 then
                    local item = bot:GetItemInSlot(manta)
                    if item and item:IsFullyCastable() then
                        bot:Action_UseAbility(item)
                        print(string.format("[DODGER] ID:%d | Casted Manta to dodge enemy spell!", bot_id))
                        return
                    end
                elseif eul ~= nil and eul >= 0 and eul <= 5 then
                    local item = bot:GetItemInSlot(eul)
                    if item and item:IsFullyCastable() then
                        bot:Action_UseAbilityOnEntity(item, bot)
                        print(string.format("[DODGER] ID:%d | Casted Eul on self to dodge!", bot_id))
                        return
                    end
                elseif blink ~= nil and blink >= 0 and blink <= 5 then
                    local item = bot:GetItemInSlot(blink)
                    if item and item:IsFullyCastable() then
                        local escape_loc = bot_loc + (bot_loc - enemy:GetLocation()) -- Блинк от врага
                        bot:Action_UseAbilityOnLocation(item, escape_loc)
                        print(string.format("[DODGER] ID:%d | Blinked away to dodge spell!", bot_id))
                        return
                    end
                end
            end
        end
    end

    -- ==================== [4/22] SPELL REFRACTION LINKER ====================
    if pos == 4 or pos == 5 then
        local lotus = bot:FindItemSlot("item_lotus_orb")
        if lotus ~= nil and lotus >= 0 and lotus <= 5 then
            local lotus_item = bot:GetItemInSlot(lotus)
            if lotus_item and lotus_item:IsFullyCastable() then
                local nearby_allies = bot:GetNearbyHeroes(900, false, BOT_MODE_NONE)
                if nearby_allies ~= nil then
                    for _, ally in ipairs(nearby_allies) do
                        if ally ~= nil and ally:IsAlive() and not ally:IsBot() then
                            -- Спасаем живого игрока-человека при фокусе
                            if ally:GetHealth() / math.max(ally:GetMaxHealth(), 1) < 0.5 then
                                bot:Action_UseAbilityOnEntity(lotus_item, ally)
                                print(string.format("[LINKER] Lotus Orb used on ally: %s!", ally:GetUnitName()))
                                return
                            end
                        end
                    end
                end
            end
        end
    end

    -- ==================== [5/22] CREEP AGGRO CONTROL ====================
    if now < 600 and not bot:IsCastingAbility() then
        local enemy_heroes = bot:GetNearbyHeroes(1000, true, BOT_MODE_NONE)
        if enemy_heroes ~= nil and #enemy_heroes > 0 then
            local nearby_creeps = bot:GetNearbyCreeps(600, true)
            if nearby_creeps ~= nil and #nearby_creeps > 0 then
                -- Атакуем любого вражеского героя на карте, чтобы вызвать агрессию крипов на себя
                bot:Action_AttackUnit(enemy_heroes[1], true)
                print(string.format("[AGGRO] ID:%d | Creep Aggro Manipulated on enemy %s!", bot_id, enemy_heroes[1]:GetUnitName()))
            end
        end
    end

    -- ==================== [6/22] ILLUSION MICRO HARASS ====================
    if bot:GetUnitName() == "npc_dota_hero_phantom_lancer" or bot:GetUnitName() == "npc_dota_hero_naga_siren" or bot:GetUnitName() == "npc_dota_hero_terrorblade" then
        local nearby_units = GetUnitList(UNIT_LIST_ALLIED_CREEPS)
        if nearby_units ~= nil then
            for _, unit in ipairs(nearby_units) do
                if unit ~= nil and unit:IsIllusion() and unit:GetPlayerID() == bot_id then
                    -- Отправляем иллюзии атаковать ближайших врагов или лагеря
                    local targets = unit:GetNearbyHeroes(1400, true, BOT_MODE_NONE)
                    if targets ~= nil and #targets > 0 then
                        unit:Action_AttackUnit(targets[1], true)
                    else
                        local neutrals = JUNGLE_CAMPS[team][1]
                        unit:Action_MoveToLocation(Vector(neutrals.x, neutrals.y, neutrals.z))
                    end
                end
            end
        end
    end

    -- ==================== [7/22] NEUTRAL ITEMS DISTRIBUTOR ====================
    local neutral_slot = bot:FindItemSlot("item_neutral_slot")
    if neutral_slot ~= nil then
        -- Проверка нейтрального предмета
        local neutral_item = bot:GetItemInSlot(neutral_slot)
        if neutral_item ~= nil then
            local item_name = neutral_item:GetName()
            -- Если оффлейнеру выпала чисто саппортская нейтралка (например, Philosopher's Stone)
            if pos == 3 and item_name == "item_philosophers_stone" then
                -- Бросаем на базу / отправляем в тайник
                bot:ActionImmediate_Courier(GetCourier(bot_id % 5), COURIER_ACTION_RETURN)
                print(string.format("[NEUTRAL] Core %s sending Philosopher's Stone back for supports!", bot:GetUnitName()))
            end
        end
    end

    -- ==================== [8/22] WARD DENIER ====================
    if (pos == 4 or pos == 5) and now > 300 then
        local nearby_enemies = bot:GetNearbyHeroes(1600, true, BOT_MODE_NONE)
        if nearby_enemies ~= nil then
            for _, enemy in ipairs(nearby_enemies) do
                -- Если вражеский саппорт скрылся во тьме на горке и вышел без варда
                if enemy:GetUnitName() == "npc_dota_hero_crystal_maiden" or enemy:GetUnitName() == "npc_dota_hero_lion" then
                    local enemy_loc = enemy:GetLocation()
                    -- Ставим Sentry для девардинга
                    local sentry = bot:FindItemSlot("item_ward_sentry")
                    if sentry ~= nil and sentry >= 0 and sentry <= 5 then
                        local sentry_item = bot:GetItemInSlot(sentry)
                        if sentry_item and sentry_item:IsFullyCastable() then
                            bot:Action_UseAbilityOnLocation(sentry_item, enemy_loc)
                            print(string.format("[WARD_DENY] Support %s dewarding spot at (%.0f, %.0f)!", bot:GetUnitName(), enemy_loc.x, enemy_loc.y))
                            return
                        end
                    end
                end
            end
        end
    end

    -- ==================== [9/22] STREAM SNIPE WARD PREDICTOR ====================
    if (pos == 4 or pos == 5) and _G.deathball_active then
        -- При пуше башни ставим вард за вышку врага для вижна телепортов
        local ward = bot:FindItemSlot("item_ward_observer")
        if ward ~= nil and ward >= 0 and ward <= 5 then
            local ward_item = bot:GetItemInSlot(ward)
            if ward_item and ward_item:IsFullyCastable() then
                local push_target = _G.deathball_target
                if push_target ~= nil then
                    local target_building = GetTower(team == 2 and 3 or 2, push_target)
                    if target_building ~= nil and target_building:IsAlive() then
                        local ward_pos = target_building:GetLocation() + Vector(team == 2 and 500 or -500, 500, 0)
                        bot:Action_UseAbilityOnLocation(ward_item, ward_pos)
                        print(string.format("[VISION] Support %s placing aggressive push ward behind tower!", bot:GetUnitName()))
                        return
                    end
                end
            end
        end
    end

    -- ==================== [10/22] AEGIS SNATCHER LOGIC ====================
    if _G.roshan_attempt_active and (pos == 1 or pos == 2 or pos == 4) then
        local nearby_neutrals = bot:GetNearbyCreeps(1000, true)
        if nearby_neutrals ~= nil then
            for _, creep in ipairs(nearby_neutrals) do
                if creep ~= nil and creep:IsAlive() and string.find(creep:GetUnitName(), "roshan") then
                    if creep:GetHealth() < 400 then
                        -- Рошан при смерти! Спамим подбор предметов
                        local items_on_ground = GetDroppedItemList()
                        if items_on_ground ~= nil then
                            for _, item in ipairs(items_on_ground) do
                                if item ~= nil and (string.find(item:GetName(), "item_aegis") or string.find(item:GetName(), "item_cheese")) then
                                    bot:Action_PickUpItem(item)
                                    print(string.format("[SNATCHER] ID:%d | Perfect Aegis Snatch Attempt!", bot_id))
                                    return
                                end
                            end
                        end
                    end
                end
            end
        end
    end

    -- ==================== [11/22] HIGH GROUND SIEGE DIRECTOR ====================
    if _G.deathball_active and now > 1800 then
        local push_target = _G.deathball_target
        if push_target ~= nil and (push_target == TOWER_TOP_3 or push_target == TOWER_MID_3 or push_target == TOWER_BOT_3) then
            -- Мы штурмуем хайграунд!
            local tower = GetTower(team == 2 and 3 or 2, push_target)
            if tower ~= nil and tower:IsAlive() then
                local t_loc = tower:GetLocation()
                if pos == 1 then
                    -- Керри бьет вышку
                    bot:Action_AttackUnit(tower, true)
                    return
                elseif pos == 3 then
                    -- Танк стоит впереди и принимает удар
                    local front_pos = t_loc + Vector(team == 2 and -200 or 200, 0, 0)
                    bot:Action_MoveToLocation(front_pos)
                    return
                elseif pos == 4 or pos == 5 then
                    -- Саппорты стоят сзади в сейве
                    local back_pos = t_loc + Vector(team == 2 and 900 or -900, 0, 0)
                    bot:Action_MoveToLocation(back_pos)
                    return
                end
            end
        end
    end

    -- ==================== [12/22] SMOKE BREAK COUNTER INITIATOR ====================
    if bot:HasModifier("modifier_item_smoke_of_deceit") then
        -- Если смок спадает из-за приближения врага
        local nearby_enemies = bot:GetNearbyHeroes(1025, true, BOT_MODE_NONE)
        if nearby_enemies ~= nil and #nearby_enemies > 0 then
            -- Смок сбит! Мгновенная контр-атака
            local bkb = bot:FindItemSlot("item_black_king_bar")
            if bkb ~= nil and bkb >= 0 and bkb <= 5 then
                local bkb_item = bot:GetItemInSlot(bkb)
                if bkb_item and bkb_item:IsFullyCastable() then
                    bot:Action_UseAbility(bkb_item)
                    print(string.format("[COUNTER_INIT] ID:%d | Smoke broken! Pro BKBs popped!", bot_id))
                end
            end
        end
    end

    -- ==================== [13/22] FOUNTAIN DIVING SAFETY ====================
    local fountain_loc = (team == 2) and Vector(7200, 6700, 384) or Vector(-7200, -6700, 384) -- Вражеский фонтан
    if GetDistance(bot_loc, fountain_loc) < 2200 then
        -- Безопасность фонтана: разворачиваемся назад
        local safe_loc = (team == 2) and Vector(4000, 4000, 256) or Vector(-4000, -4000, 256)
        bot:Action_MoveToLocation(safe_loc)
        print(string.format("[SAFETY] Hero %s prevented from fountain diving!", bot:GetUnitName()))
        return
    end

    -- ==================== [14/22] TP CANCEL INTERRUPTER ====================
    local nearby_enemies = bot:GetNearbyHeroes(800, true, BOT_MODE_NONE)
    if nearby_enemies ~= nil then
        for _, enemy in ipairs(nearby_enemies) do
            if enemy ~= nil and enemy:IsAlive() and enemy:HasModifier("modifier_teleporting") then
                -- Враг телепортируется! Прожимаем стан/безмолвие
                local stun_abil = bot:GetAbilityInSlot(0)
                if stun_abil and stun_abil:CanAbilityBeUpgraded() and stun_abil:IsFullyCastable() then
                    bot:Action_UseAbilityOnEntity(stun_abil, enemy)
                    print(string.format("[INTERRUPT] ID:%d | Interrupted enemy TP of %s!", bot_id, enemy:GetUnitName()))
                    return
                end
            end
        end
    end

    -- ==================== [15/22] PSYCHOLOGICAL TAUNT BOT ====================
    -- После убийства врага пишем в чат "БУРМАЛДА" и прожимаем таунты
    local opposing = (team == 2) and 3 or 2
    local enemy_ids = GetTeamPlayers(opposing)
    for _, eid in ipairs(enemy_ids) do
        if not IsHeroAlive(eid) then
            if _G.last_kill_time == nil then _G.last_kill_time = {} end
            if _G.last_kill_time[eid] == nil or (now - _G.last_kill_time[eid]) > 120 then
                _G.last_kill_time[eid] = now
                -- Пишем БУРМАЛДА
                bot:ActionImmediate_Chat("БУРМАЛДА", true)
                print(string.format("[PSYCHOLOGY] Tipped and Taunted enemy ID: %d with BURMALDA!", eid))
            end
        end
    end

    -- ==================== [16/22] CHAT WHEEL COORDINATOR ====================
    if _G.deathball_active and pos == 1 then
        if _G.last_chat_wheel == nil or (now - _G.last_chat_wheel) > 60 then
            _G.last_chat_wheel = now
            bot:ActionImmediate_Chat("Get Ready", false)
            print("[CHAT_WHEEL] Carry called: Get Ready for push!")
        end
    end

    -- ==================== [22/22] DIVINE RAPIER RETRIEVAL ====================
    local ground_items = GetDroppedItemList()
    if ground_items ~= nil then
        for _, item in ipairs(ground_items) do
            if item ~= nil and string.find(item:GetName(), "item_rapier") then
                -- Выпала Рапира! Все бежим поднимать
                bot:Action_PickUpItem(item)
                print(string.format("[RAPIER] Hero %s prioritized Divine Rapier retrieval!", bot:GetUnitName()))
                return
            end
        end
    end

    -- ==================== SUPPORT WARDING UTILITY AI ====================
    if (pos == 4 or pos == 5) and (now - (warding_cooldown[bot_id] or 0) > 180) then
        local ward_item = nil
        for slot = 0, 5 do
            local item = bot:GetItemInSlot(slot)
            if item and (item:GetName() == "item_ward_observer" or item:GetName() == "item_ward_dispenser") then
                ward_item = item
                break
            end
        end
        if ward_item then
            if warding_state[bot_id] == nil then
                local selected_spot = SelectWardSpot(bot, team)
                warding_state[bot_id] = { spot = selected_spot, start_time = now }
                print(string.format("[BOT_UTILITY] Support %s starting warding mission!", bot:GetUnitName()))
            end
            local target_spot = warding_state[bot_id].spot
            local dist = GetDistance(bot_loc, target_spot)
            if dist > 350 then
                bot:Action_MoveToLocation(Vector(target_spot.x, target_spot.y, target_spot.z))
                return
            else
                bot:Action_UseAbilityOnLocation(ward_item, Vector(target_spot.x, target_spot.y, target_spot.z))
                warding_state[bot_id] = nil
                warding_cooldown[bot_id] = now
                print(string.format("[BOT_UTILITY] Support %s successfully placed observer ward!", bot:GetUnitName()))
                return
            end
        else
            warding_state[bot_id] = nil
        end
    end

    -- ==================== [38/22] PRO CAMP PULLING & EQUILIBRIUM (Отводы и баланс линии) ====================
    if _G.pull_state == nil then _G.pull_state = {} end
    if _G.pull_target_camp == nil then _G.pull_target_camp = {} end
    if _G.pull_last_time == nil then _G.pull_last_time = {} end
    
    local sec = now % 60
    local is_support = (pos == 4 or pos == 5)
    
    if is_support and now > 90 and now < 600 then
        local camp_info = PULL_CAMPS[team]
        if camp_info ~= nil then
            local current_state = _G.pull_state[bot_id] or "PULL_STATE_NONE"
            local dist_to_camp = GetDistance(bot_loc, camp_info.camp)
            
            local nearby_enemies = bot:GetNearbyHeroes(1000, true, BOT_MODE_NONE)
            if nearby_enemies ~= nil and #nearby_enemies > 0 then
                if current_state ~= "PULL_STATE_NONE" then
                    _G.pull_state[bot_id] = "PULL_STATE_NONE"
                    print(string.format("[PRO_PULL] Support %s aborted pull due to enemy threat nearby!", bot:GetUnitName()))
                end
            else
                if current_state == "PULL_STATE_NONE" then
                    if (sec >= 8 and sec <= 12) or (sec >= 38 and sec <= 42) then
                        _G.pull_state[bot_id] = "PULL_STATE_APPROACHING"
                        print(string.format("[PRO_PULL] Support %s starting approach to small camp at sec %d", bot:GetUnitName(), sec))
                    end
                
                elseif current_state == "PULL_STATE_APPROACHING" then
                    if dist_to_camp > 200 then
                        bot:Action_MoveToLocation(camp_info.camp)
                        return
                    else
                        _G.pull_state[bot_id] = "PULL_STATE_WAITING_FOR_HIT"
                        print(string.format("[PRO_PULL] Support %s arrived at small camp, waiting for agro timer", bot:GetUnitName()))
                    end
                
                elseif current_state == "PULL_STATE_WAITING_FOR_HIT" then
                    if sec == 15 or sec == 45 or sec == 16 or sec == 46 then
                        local neutrals = bot:GetNearbyCreeps(600, true)
                        if neutrals ~= nil and #neutrals > 0 then
                            bot:Action_AttackUnit(neutrals[1], true)
                            _G.pull_state[bot_id] = "PULL_STATE_PULLING"
                            _G.pull_last_time[bot_id] = now
                            print(string.format("[PRO_PULL] Support %s attack-aggroed neutral creep: %s", bot:GetUnitName(), neutrals[1]:GetUnitName()))
                            return
                        else
                            _G.pull_state[bot_id] = "PULL_STATE_NONE"
                            print(string.format("[PRO_PULL] Support %s found small camp empty! Resetting state.", bot:GetUnitName()))
                        end
                    elseif (sec > 16 and sec < 35) or (sec > 46 and sec < 5) then
                        _G.pull_state[bot_id] = "PULL_STATE_NONE"
                    end
                
                elseif current_state == "PULL_STATE_PULLING" then
                    local elapsed = now - (_G.pull_last_time[bot_id] or now)
                    if elapsed < 8.5 then
                        bot:Action_MoveToLocation(camp_info.pull_loc)
                        
                        local allied_lane_creeps = bot:GetNearbyCreeps(700, false)
                        local neutral_creeps = bot:GetNearbyCreeps(700, true)
                        if allied_lane_creeps ~= nil and #allied_lane_creeps > 0 and neutral_creeps ~= nil and #neutral_creeps > 0 then
                            for _, ac in ipairs(allied_lane_creeps) do
                                if ac:GetAttackTarget() ~= nil then
                                    _G.pull_state[bot_id] = "PULL_STATE_COMPLETED"
                                    print(string.format("[PRO_PULL] Support %s SUCCESS! Creep wave pulled successfully!", bot:GetUnitName()))
                                    break
                                end
                            end
                        end
                        return
                    else
                        _G.pull_state[bot_id] = "PULL_STATE_NONE"
                        print(string.format("[PRO_PULL] Support %s pull timeout. Resetting.", bot:GetUnitName()))
                    end
                    
                elseif current_state == "PULL_STATE_COMPLETED" then
                    local neutral_creeps = bot:GetNearbyCreeps(600, true)
                    if neutral_creeps ~= nil and #neutral_creeps > 0 then
                        bot:Action_AttackUnit(neutral_creeps[1], true)
                        return
                    else
                        _G.pull_state[bot_id] = "PULL_STATE_NONE"
                    end
                end
            end
        end
    end
    
    if not is_support and now < 600 and not bot:IsCastingAbility() then
        local nearby_allied_creeps = bot:GetNearbyCreeps(700, false)
        local nearby_enemy_creeps = bot:GetNearbyCreeps(700, true)
        
        local enemy_towers = bot:GetNearbyTowers(1300, true)
        local is_pushed = (enemy_towers ~= nil and #enemy_towers > 0)
        
        if is_pushed then
            if nearby_enemy_creeps ~= nil and #nearby_enemy_creeps > 0 then
                local target_creep = nil
                local min_hp = 99999
                for _, ec in ipairs(nearby_enemy_creeps) do
                    if ec ~= nil and ec:IsAlive() then
                        local hp = ec:GetHealth()
                        if hp < min_hp then
                            min_hp = hp
                            target_creep = ec
                        end
                    end
                end
                
                local dmg = bot:GetAttackDamage()
                if target_creep ~= nil and min_hp <= (dmg + 45) then
                    bot:Action_AttackUnit(target_creep, true)
                    print(string.format("[PRO_EQUILIBRIUM] Core %s doing surgical last-hit under enemy tower pressure!", bot:GetUnitName()))
                    return
                end
            end
        end
        
        if nearby_allied_creeps ~= nil and #nearby_allied_creeps > 0 then
            local best_deny_creep = nil
            local min_hp = 99999
            for _, ac in ipairs(nearby_allied_creeps) do
                if ac ~= nil and ac:IsAlive() then
                    local hp = ac:GetHealth()
                    local max_hp = ac:GetMaxHealth()
                    if hp < (max_hp * 0.5) and hp < min_hp then
                        min_hp = hp
                        best_deny_creep = ac
                    end
                end
            end
            
            if best_deny_creep ~= nil then
                bot:Action_AttackUnit(best_deny_creep, true)
                print(string.format("[PRO_EQUILIBRIUM] Core %s aggressively keeping lane balance, denying allied creep at %d HP!", bot:GetUnitName(), min_hp))
                return
            end
        end
    end

    -- ==================== [41/22] OUTPOST CONTESTING (Захват аванпостов) ====================
    if _G.outpost_assignment == nil then _G.outpost_assignment = {} end
    if _G.outpost_last_check == nil then _G.outpost_last_check = 0 end
    
    local outpost_locations = {
        Vector(-3050, -4500, 256),
        Vector(3050, 4500, 256),
        Vector(-1900, -2000, 256),
        Vector(1900, 2000, 256)
    }
    
    if now - _G.outpost_last_check > 30 then
        _G.outpost_last_check = now
        for pid, assignment in pairs(_G.outpost_assignment) do
            if assignment ~= nil and now - assignment.time > 90 then
                _G.outpost_assignment[pid] = nil
            end
        end
    end
    
    if is_support and not bot:IsCastingAbility() and not _G.deathball_active then
        local assigned_spot = _G.outpost_assignment[bot_id]
        
        if assigned_spot == nil then
            for idx, loc in ipairs(outpost_locations) do
                local dist = GetDistance(bot_loc, loc)
                if dist < 4500 then
                    local already_taken = false
                    for pid, assign in pairs(_G.outpost_assignment) do
                        if assign ~= nil and assign.idx == idx and pid ~= bot_id then
                            already_taken = true
                        end
                    end
                    
                    if not already_taken then
                        _G.outpost_assignment[bot_id] = { idx = idx, loc = loc, time = now }
                        print(string.format("[OUTPOST] Support %s assigned to contest Outpost #%d at (%.0f, %.0f)!", bot:GetUnitName(), idx, loc.x, loc.y))
                        break
                    end
                end
            end
        end
        
        assigned_spot = _G.outpost_assignment[bot_id]
        if assigned_spot ~= nil then
            local target_loc = assigned_spot.loc
            local dist = GetDistance(bot_loc, target_loc)
            
            if dist < 300 then
                local nearby_units = GetUnitList(UNIT_LIST_ALL)
                local outpost_unit = nil
                if nearby_units ~= nil then
                    for _, unit in ipairs(nearby_units) do
                        if unit ~= nil and string.find(string.lower(unit:GetUnitName()), "outpost") then
                            outpost_unit = unit
                            break
                        end
                    end
                end
                
                if outpost_unit ~= nil then
                    bot:Action_AttackUnit(outpost_unit, true)
                    if outpost_unit:GetTeam() == team then
                        _G.outpost_assignment[bot_id] = nil
                        print(string.format("[OUTPOST] Support %s successfully captured outpost!", bot:GetUnitName()))
                    end
                    return
                else
                    bot:Action_MoveToLocation(target_loc)
                    return
                end
            else
                bot:Action_MoveToLocation(target_loc)
                return
            end
        end
    else
        _G.outpost_assignment[bot_id] = nil
    end

    -- ==================== CARRY JUNGLE STACKING (XX:53 to XX:58) ====================
    if pos == 1 and now > 300 then
        local sec = now % 60
        local is_stack_time = (sec >= 52 and sec <= 58)
        
        if is_stack_time then
            if current_jungle_camp[bot_id] == nil then
                current_jungle_camp[bot_id] = { idx = 1, arrive_time = 0, last_change = now }
            end
            local camp = JUNGLE_CAMPS[team][current_jungle_camp[bot_id].idx]
            local dist = GetDistance(bot_loc, camp)
            
            if dist <= 800 then
                local neutral_creeps = bot:GetNearbyCreeps(800, true)
                local has_neutrals = false
                if neutral_creeps ~= nil then
                    for _, creep in ipairs(neutral_creeps) do
                        if creep and creep:IsAlive() and not creep:IsHero() then
                            has_neutrals = true
                            break
                        end
                    end
                end
                
                if has_neutrals then
                    if sec == 52 or sec == 53 or sec == 54 then
                        local nearest_neutral = nil
                        local min_c_dist = 99999
                        for _, creep in ipairs(neutral_creeps) do
                            if creep and creep:IsAlive() and not creep:IsHero() then
                                local c_dist = GetDistance(bot_loc, creep:GetLocation())
                                if c_dist < min_c_dist then
                                    min_c_dist = c_dist
                                    nearest_neutral = creep
                                end
                            end
                        end
                        if nearest_neutral then
                            bot:Action_AttackUnit(nearest_neutral, true)
                            print(string.format("[BOT_UTILITY] Carry %s attack-aggroing neutrals for stack!", bot:GetUnitName()))
                            return
                        end
                    else
                        -- Pull away towards allied fountain
                        local fountain_loc = (team == 2) and Vector(-7200, -6700, 384) or Vector(7200, 6700, 384)
                        local dir_x = fountain_loc.x - camp.x
                        local dir_y = fountain_loc.y - camp.y
                        local len = math.sqrt(dir_x^2 + dir_y^2)
                        local pull_loc = Vector(camp.x + (dir_x / len) * 1000, camp.y + (dir_y / len) * 1000, camp.z)
                        bot:Action_MoveToLocation(pull_loc)
                        print(string.format("[BOT_UTILITY] Carry %s pulling camp to stack!", bot:GetUnitName()))
                        return
                    end
                end
            end
        end
    end

    -- ==================== [1/8] BUYBACK LOGIC (Высший приоритет) ====================
    if not bot:IsAlive() and now > 1500 then
        if _G.buyback_used == nil then _G.buyback_used = {} end
        local bb_cost = bot:GetBuybackCost()
        local bb_cd = bot:GetBuybackCooldown()
        local gold = bot:GetGold()
        local can_buyback = (bb_cd <= 0) and (gold >= bb_cost)

        if can_buyback and (_G.buyback_used[bot_id] == nil or (now - _G.buyback_used[bot_id]) > 300) then
            local dead_allies = 0
            local alive_allies = 0
            for pid = 0, 4 do
                local member = GetTeamMember(pid + 1)
                if member ~= nil then
                    if not member:IsAlive() then
                        dead_allies = dead_allies + 1
                    else
                        alive_allies = alive_allies + 1
                    end
                end
            end

            local opposing = (team == 2) and 3 or 2
            local ancient_under_attack = false
            local t3_under_attack = false
            local barracks_under_attack = false

            local ancient = GetAncient(team)
            if ancient ~= nil and ancient:IsAlive() then
                local ancient_attackers = ancient:GetNearbyHeroes(1300, true, BOT_MODE_NONE)
                if ancient_attackers ~= nil and #ancient_attackers > 0 then
                    ancient_under_attack = true
                end
            end

            local t3_towers = {
                GetTower(team, TOWER_TOP_3),
                GetTower(team, TOWER_MID_3),
                GetTower(team, TOWER_BOT_3)
            }
            for _, t3 in ipairs(t3_towers) do
                if t3 ~= nil and t3:IsAlive() then
                    local attackers = t3:GetNearbyHeroes(1300, true, BOT_MODE_NONE)
                    if attackers ~= nil and #attackers > 0 then
                        t3_under_attack = true
                        break
                    end
                end
            end

            local barracks_list = {
                GetBarracks(team, BARRACKS_TOP_MELEE), GetBarracks(team, BARRACKS_TOP_RANGED),
                GetBarracks(team, BARRACKS_MID_MELEE), GetBarracks(team, BARRACKS_MID_RANGED),
                GetBarracks(team, BARRACKS_BOT_MELEE), GetBarracks(team, BARRACKS_BOT_RANGED)
            }
            for _, rax in ipairs(barracks_list) do
                if rax ~= nil and rax:IsAlive() then
                    local attackers = rax:GetNearbyHeroes(1300, true, BOT_MODE_NONE)
                    if attackers ~= nil and #attackers > 0 then
                        barracks_under_attack = true
                        break
                    end
                end
            end

            local should_buyback = false
            local buyback_reason = ""

            if ancient_under_attack then
                should_buyback = true
                buyback_reason = "ANCIENT UNDER ATTACK"
            elseif (t3_under_attack or barracks_under_attack) and dead_allies >= 2 then
                should_buyback = true
                buyback_reason = "T3/BARRACKS under attack"
            end

            if should_buyback then
                bot:ActionImmediate_Buyback()
                _G.buyback_used[bot_id] = now
                print(string.format("[BUYBACK] Hero %s BUYBACK! Reason: %s", bot:GetUnitName(), buyback_reason))
                return
            end
        end
    end

    -- ==================== [2/8] TP REACTIONS ====================
    if _G.tower_health_history == nil then _G.tower_health_history = {} end
    if _G.tp_defense_cooldown == nil then _G.tp_defense_cooldown = {} end
    if _G.tp_defense_assigned == nil then _G.tp_defense_assigned = {} end

    local all_tower_indices = {
        TOWER_TOP_1, TOWER_MID_1, TOWER_BOT_1,
        TOWER_TOP_2, TOWER_MID_2, TOWER_BOT_2,
        TOWER_TOP_3, TOWER_MID_3, TOWER_BOT_3
    }

    for _, tid in ipairs(all_tower_indices) do
        local tower = GetTower(team, tid)
        if tower ~= nil and tower:IsAlive() then
            local t_hp = tower:GetHealth()
            local t_max = tower:GetMaxHealth()
            local t_pct = t_hp / math.max(t_max, 1)

            if _G.tower_health_history[tid] == nil then
                _G.tower_health_history[tid] = { hp = t_hp, time = now }
            end

            local history = _G.tower_health_history[tid]
            local hp_diff = history.hp - t_hp

            if (now - history.time) > 8.0 then
                _G.tower_health_history[tid] = { hp = t_hp, time = now }
            end

            if hp_diff > (t_max * 0.25) and t_pct > 0.15 and (now - (_G.tp_defense_cooldown[tid] or 0)) > 60 then
                if _G.tp_defense_assigned[tid] == nil then
                    local best_defender = nil
                    local min_dist = 999999
                    local tower_loc = tower:GetLocation()

                    for pid = 0, 4 do
                        local member = GetTeamMember(pid + 1)
                        if member ~= nil and member:IsAlive() and member:GetPlayerID() ~= bot_id then
                            local d = GetDistance(member:GetLocation(), tower_loc)
                            if d > 3000 and d < min_dist then
                                local tp_slot = member:FindItemSlot("item_tpscroll")
                                if tp_slot ~= nil and tp_slot >= 0 then
                                    min_dist = d
                                    best_defender = member
                                end
                            end
                        end
                    end

                    if best_defender ~= nil then
                        _G.tp_defense_assigned[tid] = best_defender:GetPlayerID()
                        _G.tp_defense_cooldown[tid] = now
                        print(string.format("[TP_DEFENSE] Tower %d is dived! Assigned defender: %s", tid, best_defender:GetUnitName()))
                    end
                end
            end

            if _G.tp_defense_assigned[tid] == bot_id then
                local tp_slot = bot:FindItemSlot("item_tpscroll")
                if tp_slot ~= nil and tp_slot >= 0 then
                    local tp_item = bot:GetItemInSlot(tp_slot)
                    if tp_item ~= nil and tp_item:IsFullyCastable() then
                        bot:Action_UseAbilityOnLocation(tp_item, tower:GetLocation())
                        _G.tp_defense_assigned[tid] = nil
                        print(string.format("[TP_DEFENSE] %s executing TP defense for tower %d!", bot:GetUnitName(), tid))
                        return
                    end
                end
            end
        end
    end

    -- ==================== [3/8] BOUNTY RUNE CONTESTING ====================
    if _G.bounty_rune_assignments == nil then _G.bounty_rune_assignments = {} end
    local bounty_locations = {
        Vector(-2100, 1200, 128),
        Vector(2100, -1200, 128),
        Vector(4100, -1600, 128),
        Vector(-4100, 1600, 128)
    }

    local sec = now % 180
    local is_rune_spawn_near = (sec >= 160 or sec <= 15)
    
    if is_rune_spawn_near and (pos == 4 or pos == 5) then
        local assigned_rune_idx = _G.bounty_rune_assignments[bot_id]
        if assigned_rune_idx == nil then
            local min_r_dist = 99999
            local best_r_idx = 1
            for idx, r_loc in ipairs(bounty_locations) do
                local rd = GetDistance(bot_loc, r_loc)
                if rd < min_r_dist then
                    local already_assigned = false
                    for pid, ridx in pairs(_G.bounty_rune_assignments) do
                        if ridx == idx and pid ~= bot_id then already_assigned = true end
                    end
                    if not already_assigned then
                        min_r_dist = rd
                        best_r_idx = idx
                    end
                end
            end
            _G.bounty_rune_assignments[bot_id] = best_r_idx
        end

        local r_idx = _G.bounty_rune_assignments[bot_id]
        if r_idx ~= nil then
            local target_rune_loc = bounty_locations[r_idx]
            local dist = GetDistance(bot_loc, target_rune_loc)
            if dist > 150 then
                bot:Action_MoveToLocation(target_rune_loc)
                return
            end
        end
    else
        _G.bounty_rune_assignments[bot_id] = nil
    end

    -- ==================== [4/8] SMOKE GANKS ====================
    if _G.smoke_active == nil then _G.smoke_active = false end
    if _G.smoke_leader == nil then _G.smoke_leader = nil end
    if _G.smoke_target == nil then _G.smoke_target = nil end
    if _G.smoke_used_time == nil then _G.smoke_used_time = 0 end

    if now > 600 and (now - _G.smoke_used_time) > 180 and not _G.smoke_active then
        if pos == 4 then
            local smoke_slot = bot:FindItemSlot("item_smoke_of_deceit")
            if smoke_slot ~= nil and smoke_slot >= 0 then
                local smoke_item = bot:GetItemInSlot(smoke_slot)
                if smoke_item and smoke_item:IsFullyCastable() then
                    local nearby_allies = bot:GetNearbyHeroes(1200, false, BOT_MODE_NONE)
                    local ally_count = 0
                    if nearby_allies ~= nil then
                        for _, ally in ipairs(nearby_allies) do
                            if ally ~= nil and ally:IsAlive() then ally_count = ally_count + 1 end
                        end
                    end

                    if ally_count >= 2 then
                        bot:Action_UseAbility(smoke_item)
                        _G.smoke_active = true
                        _G.smoke_leader = bot_id
                        _G.smoke_used_time = now
                        print(string.format("[SMOKE] %s activated SMOKE OF DECEIT with %d allies nearby!", bot:GetUnitName(), ally_count))
                        return
                    end
                end
            end
        end
    end

    -- ==================== [5/8] DEATHBALL PUSH ====================
    if _G.enemy_death_tracker == nil then _G.enemy_death_tracker = {} end
    if _G.deathball_active == nil then _G.deathball_active = false end
    if _G.deathball_target == nil then _G.deathball_target = nil end

    local opposing_team = (team == 2) and 3 or 2
    local opposing_ids = GetTeamPlayers(opposing_team)
    local dead_enemies_count = 0
    local est_respawn_time = 25 + (now / 60) * 1.5

    for _, eid in ipairs(opposing_ids) do
        if not IsHeroAlive(eid) then
            if _G.enemy_death_tracker[eid] == nil then
                _G.enemy_death_tracker[eid] = now
            end
            local death_time = _G.enemy_death_tracker[eid]
            if (now - death_time) < est_respawn_time then
                dead_enemies_count = dead_enemies_count + 1
            end
        else
            _G.enemy_death_tracker[eid] = nil
        end
    end

    if dead_enemies_count >= 2 and not _G.deathball_active then
        _G.deathball_active = true
        _G.deathball_start_time = now
        local push_priority = {
            TOWER_MID_1, TOWER_TOP_1, TOWER_BOT_1,
            TOWER_MID_2, TOWER_TOP_2, TOWER_BOT_2,
            TOWER_MID_3, TOWER_TOP_3, TOWER_BOT_3
        }
        for _, tid in ipairs(push_priority) do
            local tower = GetTower(opposing_team, tid)
            if tower ~= nil and tower:IsAlive() then
                _G.deathball_target = tid
                break
            end
        end
        print(string.format("[DEATHBALL] 2+ enemies dead (%d total)! Initiating team push targeting tower %d!", dead_enemies_count, _G.deathball_target or 0))
    end

    if _G.deathball_active then
        if dead_enemies_count == 0 or (now - (_G.deathball_start_time or 0)) > 45 then
            _G.deathball_active = false
            _G.deathball_target = nil
            print("[DEATHBALL] Push ended (enemies respawned or timeout)")
        elseif _G.deathball_target ~= nil then
            local target_tower = GetTower(opposing_team, _G.deathball_target)
            if target_tower ~= nil and target_tower:IsAlive() then
                bot:Action_MoveToLocation(target_tower:GetLocation())
                return
            else
                _G.deathball_active = false
                _G.deathball_target = nil
            end
        end
    end

    -- ==================== [6/8] GANK SQUADS ====================
    if _G.gank_squad_active == nil then _G.gank_squad_active = false end
    if _G.gank_squad_target == nil then _G.gank_squad_target = nil end
    if _G.gank_squad_last_time == nil then _G.gank_squad_last_time = 0 end
    if _G.gank_squad_target_lost == nil then _G.gank_squad_target_lost = 0 end

    if now > 480 and (pos == 2 or pos == 4) then
        if not _G.gank_squad_active and (now - _G.gank_squad_last_time) > 90 then
            if pos == 2 then
                local visible_enemies = bot:GetNearbyHeroes(99999, true, BOT_MODE_NONE)
                local best_gank_target = nil
                local best_gank_score = 0

                if visible_enemies ~= nil then
                    for _, enemy in ipairs(visible_enemies) do
                        if enemy ~= nil and enemy:IsAlive() then
                            local score = 0
                            local e_hp_pct = enemy:GetHealth() / math.max(enemy:GetMaxHealth(), 1)
                            local e_loc = enemy:GetLocation()

                            score = score + math.floor((1.0 - e_hp_pct) * 50)

                            local closest_enemy_tower_dist = 999999
                            for _, twr_idx in ipairs({TOWER_TOP_1, TOWER_MID_1, TOWER_BOT_1, TOWER_TOP_2, TOWER_MID_2, TOWER_BOT_2}) do
                                local e_twr = GetTower(opposing_team, twr_idx)
                                if e_twr ~= nil and e_twr:IsAlive() then
                                    local td = GetDistance(e_loc, e_twr:GetLocation())
                                    if td < closest_enemy_tower_dist then
                                        closest_enemy_tower_dist = td
                                    end
                                end
                            end
                            if closest_enemy_tower_dist > 2000 then
                                score = score + 30
                            elseif closest_enemy_tower_dist > 1200 then
                                score = score + 15
                            end

                            local enemy_allies_nearby = enemy:GetNearbyHeroes(1500, false, BOT_MODE_NONE)
                            local enemy_allies_count = 0
                            if enemy_allies_nearby ~= nil then
                                for _, ea in ipairs(enemy_allies_nearby) do
                                    if ea ~= nil and ea:IsAlive() and ea:GetPlayerID() ~= enemy:GetPlayerID() then
                                        enemy_allies_count = enemy_allies_count + 1
                                    end
                                end
                            end
                            if enemy_allies_count == 0 then
                                score = score + 40
                            elseif enemy_allies_count == 1 then
                                score = score + 15
                            end

                            if score > best_gank_score and score > 60 then
                                best_gank_score = score
                                best_gank_target = enemy
                            end
                        end
                    end
                end

                if best_gank_target ~= nil then
                    _G.gank_squad_active = true
                    _G.gank_squad_target = best_gank_target:GetPlayerID()
                    _G.gank_squad_target_name = best_gank_target:GetUnitName()
                    _G.gank_squad_start_time = now
                    _G.gank_squad_target_lost = 0
                    print(string.format("[GANK] SQUAD ACTIVATED! Target: %s", best_gank_target:GetUnitName()))
                end
            end
        end

        if _G.gank_squad_active and _G.gank_squad_target ~= nil then
            if _G.gank_squad_start_time ~= nil and (now - _G.gank_squad_start_time) > 30 then
                _G.gank_squad_active = false
                _G.gank_squad_target = nil
                _G.gank_squad_last_time = now
            else
                local gank_target_unit = nil
                local visible_enemies = bot:GetNearbyHeroes(99999, true, BOT_MODE_NONE)
                if visible_enemies ~= nil then
                    for _, enemy in ipairs(visible_enemies) do
                        if enemy ~= nil and enemy:IsAlive() and enemy:GetPlayerID() == _G.gank_squad_target then
                            gank_target_unit = enemy
                            break
                        end
                    end
                end

                if gank_target_unit ~= nil then
                    _G.gank_squad_target_lost = 0
                    local target_loc = gank_target_unit:GetLocation()
                    local dist_to_target = GetDistance(bot_loc, target_loc)

                    local squad_partner = nil
                    local partner_pos = (pos == 2) and 4 or 2
                    local nearby_allies = bot:GetNearbyHeroes(99999, false, BOT_MODE_NONE)
                    if nearby_allies ~= nil then
                        for _, ally in ipairs(nearby_allies) do
                            if ally ~= nil and ally:IsAlive() then
                                local ap = GetBotPosition(ally)
                                if ap == partner_pos then
                                    squad_partner = ally
                                    break
                                end
                            end
                        end
                    end

                    if squad_partner ~= nil then
                        local partner_dist = GetDistance(bot_loc, squad_partner:GetLocation())
                        if partner_dist > 1500 then
                            bot:Action_MoveToLocation(squad_partner:GetLocation())
                            return
                        end
                    end

                    bot:Action_MoveToLocation(target_loc)
                    return
                else
                    if _G.gank_squad_target_lost == 0 then
                        _G.gank_squad_target_lost = now
                    end
                    if (now - _G.gank_squad_target_lost) > 5 then
                        _G.gank_squad_active = false
                        _G.gank_squad_target = nil
                        _G.gank_squad_last_time = now
                    end
                end
            end
        end
    end

    -- ==================== [7/8] ROSHAN TIMER + CONTEST ====================
    if _G.roshan_killed_time == nil then _G.roshan_killed_time = -999 end
    if _G.roshan_attempt_cooldown == nil then _G.roshan_attempt_cooldown = 0 end
    if _G.roshan_attempt_active == nil then _G.roshan_attempt_active = false end

    local ROSHAN_PIT = Vector(-2350, 1800, 128)
    local ROSHAN_MIN_RESPAWN = 480
    local ROSHAN_MAX_RESPAWN = 660

    local time_since_rosh_death = now - _G.roshan_killed_time
    local rosh_probably_alive = (time_since_rosh_death > ROSHAN_MIN_RESPAWN) or (_G.roshan_killed_time < 0)

    if rosh_probably_alive and now > 900 and (now - _G.roshan_attempt_cooldown) > 180 then
        local our_lh_total = 0
        local enemy_lh_total = 5 * (now / 60) * 5

        for pid = 0, 4 do
            local member = GetTeamMember(pid + 1)
            if member ~= nil then
                our_lh_total = our_lh_total + member:GetLastHits()
            end
        end

        local gold_advantage = (our_lh_total - enemy_lh_total) * 40

        if gold_advantage > 2000 then
            if pos == 1 or pos == 2 or pos == 3 then
                local dist_to_rosh = GetDistance(bot_loc, ROSHAN_PIT)
                if dist_to_rosh > 500 then
                    bot:Action_MoveToLocation(ROSHAN_PIT)
                    return
                else
                    local nearby_neutrals = bot:GetNearbyCreeps(1000, true)
                    if nearby_neutrals ~= nil then
                        for _, creep in ipairs(nearby_neutrals) do
                            if creep ~= nil and creep:IsAlive() and string.find(creep:GetUnitName(), "roshan") then
                                bot:Action_AttackUnit(creep, true)
                                _G.roshan_attempt_active = true
                                if creep:GetHealth() <= 0 then
                                    _G.roshan_killed_time = now
                                    _G.roshan_attempt_active = false
                                    _G.roshan_attempt_cooldown = now
                                end
                                return
                            end
                        end
                    end
                    _G.roshan_attempt_cooldown = now
                    _G.roshan_attempt_active = false
                end
            elseif pos == 4 or pos == 5 then
                local ward_item = nil
                for slot = 0, 5 do
                    local item = bot:GetItemInSlot(slot)
                    if item and (item:GetName() == "item_ward_observer" or item:GetName() == "item_ward_sentry") then
                        ward_item = item
                        break
                    end
                end
                local rosh_ward_spots = {
                    Vector(-1800, 2600, 128),
                    Vector(-3100, 1400, 128)
                }
                local rosh_ward_spot = rosh_ward_spots[(bot_id % #rosh_ward_spots) + 1]
                local dist_to_ward = GetDistance(bot_loc, rosh_ward_spot)

                if ward_item ~= nil and dist_to_ward > 300 then
                    bot:Action_MoveToLocation(rosh_ward_spot)
                    return
                elseif ward_item ~= nil and dist_to_ward <= 300 then
                    bot:Action_UseAbilityOnLocation(ward_item, rosh_ward_spot)
                    return
                else
                    local guard_pos = Vector(-2800, 1200, 128)
                    bot:Action_MoveToLocation(guard_pos)
                    return
                end
            end
        end
    end

    -- ==================== [8/8] POWER SPIKE DETECTION ====================
    if _G.power_spike_heroes == nil then _G.power_spike_heroes = {} end
    if _G.hero_items_snapshot == nil then _G.hero_items_snapshot = {} end
    if _G.power_spike_last_check == nil then _G.power_spike_last_check = 0 end

    local KEY_ITEMS = {
        ["item_blink"] = true,
        ["item_black_king_bar"] = true,
        ["item_ultimate_scepter"] = true,
        ["item_travel_boots"] = true,
        ["item_orchid"] = true,
        ["item_desolator"] = true,
        ["item_radiance"] = true,
        ["item_battle_fury"] = true,
        ["item_monkey_king_bar"] = true,
        ["item_assault"] = true,
        ["item_heart"] = true,
        ["item_satanic"] = true
    }

    if (now - _G.power_spike_last_check) > 5 then
        _G.power_spike_last_check = now
        if _G.hero_items_snapshot[bot_id] == nil then _G.hero_items_snapshot[bot_id] = {} end

        local current_items = {}
        for slot = 0, 8 do
            local item = bot:GetItemInSlot(slot)
            if item ~= nil then current_items[item:GetName()] = true end
        end

        local prev_items = _G.hero_items_snapshot[bot_id]
        for item_name, _ in pairs(current_items) do
            if KEY_ITEMS[item_name] and not prev_items[item_name] then
                _G.power_spike_heroes[bot_id] = {
                    item = item_name,
                    time = now,
                    duration = 90,
                    hero_name = bot:GetUnitName()
                }
                print(string.format("[POWER_SPIKE] %s got key item: %s!", bot:GetUnitName(), item_name))
            end
        end
        _G.hero_items_snapshot[bot_id] = current_items
    end

    for pid, spike_data in pairs(_G.power_spike_heroes) do
        if spike_data ~= nil and (now - spike_data.time) > spike_data.duration then
            _G.power_spike_heroes[pid] = nil
        end
    end

    if _G.power_spike_heroes[bot_id] ~= nil then
        local visible_enemies = bot:GetNearbyHeroes(3000, true, BOT_MODE_NONE)
        if visible_enemies ~= nil and #visible_enemies > 0 then
            local weakest_enemy = nil
            local weakest_hp = 999999
            for _, enemy in ipairs(visible_enemies) do
                if enemy ~= nil and enemy:IsAlive() then
                    local e_hp = enemy:GetHealth()
                    if e_hp < weakest_hp then
                        weakest_hp = e_hp
                        weakest_enemy = enemy
                    end
                end
            end
            if weakest_enemy ~= nil then
                local dist = GetDistance(bot_loc, weakest_enemy:GetLocation())
                if dist > 500 then
                    bot:Action_MoveToLocation(weakest_enemy:GetLocation())
                    return
                end
    -- ==================== [23/22] MID LANE EXTREME DOMINANCE (Вынос ногами в миду) ====================
    if pos == 2 and now < 900 then
        -- 1. Контроль активных рун (каждые 2 минуты: 2:00, 4:00, 6:00, 8:00)
        local sec = now % 120
        local is_rune_time = (sec >= 105 or sec <= 10)
        if is_rune_time then
            local rune_spots = {
                Vector(-1600, 1600, 128), -- Top River Rune
                Vector(1600, -1600, 128)  -- Bot River Rune
            }
            -- Выбираем руну на основе PlayerID
            local r_spot = rune_spots[(bot_id % #rune_spots) + 1]
            local dist = GetDistance(bot_loc, r_spot)
            if dist > 150 then
                bot:Action_MoveToLocation(r_spot)
                print(string.format("[MID_DOMINANCE] %s (pos 2) rushing to River Rune spot! Dist: %.0f", bot:GetUnitName(), dist))
                return
            else
                -- Ищем и подбираем руну
                local runes = GetDroppedItemList()
                if runes ~= nil then
                    for _, r in ipairs(runes) do
                        if r ~= nil and string.find(r:GetName(), "item_rune") then
                            bot:Action_PickUpItem(r)
                            print(string.format("[MID_DOMINANCE] %s snatched the river rune!", bot:GetUnitName()))
                            return
                        end
                    end
                end
            end
        end

        -- 2. Умное добивание своих крипов (Deny) для лишения игрока опыта
        local ally_creeps = bot:GetNearbyCreeps(600, false)
        if ally_creeps ~= nil and #ally_creeps > 0 then
            local lowest_hp_creep = nil
            local lowest_hp = 99999
            for _, creep in ipairs(ally_creeps) do
                if creep ~= nil and creep:IsAlive() then
                    local chp = creep:GetHealth()
                    local cmax = creep:GetMaxHealth()
                    -- Если здоровье крипа ниже 50%
                    if chp < (cmax * 0.5) and chp < lowest_hp then
                        lowest_hp = chp
                        lowest_hp_creep = creep
                    end
                end
            end
            -- Если у крипа критически мало здоровья, жестко добиваем его
            if lowest_hp_creep ~= nil and lowest_hp < 80 then
                bot:Action_AttackUnit(lowest_hp_creep, true)
                print(string.format("[MID_DOMINANCE] %s DENYING allied creep at %d HP!", bot:GetUnitName(), lowest_hp))
                return
            end
        end

        -- 3. Безупречный авто-харасс врага в миду при его замахе
        local enemy_mid = bot:GetNearbyHeroes(800, true, BOT_MODE_NONE)
        if enemy_mid ~= nil and #enemy_mid > 0 and enemy_mid[1]:IsAlive() then
            local target = enemy_mid[1]
            -- Если враг замахивается на атаку или кастует
            if target:IsCastingAbility() or target:WasRecentlyDamagedByAnyHero(1.0) then
                -- Мгновенно прожимаем основной нюк (Slot 0 или Slot 1)
                local harass_spell = bot:GetAbilityInSlot(0)
                if harass_spell and harass_spell:IsFullyCastable() then
                    bot:Action_UseAbilityOnEntity(harass_spell, target)
                    print(string.format("[MID_DOMINANCE] AUTO-HARASS! Casted spell %s on enemy %s!", harass_spell:GetName(), target:GetUnitName()))
                    return
                end
                -- Или жестко бьем с руки
                bot:Action_AttackUnit(target, true)
                return
            end
        end
    end

    -- ==================== [24/22] DYNAMIC JUNGLING FARM PATHFINDER (Фарм-паттерны по лесу) ====================
    if (pos == 1 or pos == 2 or pos == 3) and now > 360 then
        local nearby_creeps = bot:GetNearbyCreeps(800, true)
        local nearby_enemy_heroes = bot:GetNearbyHeroes(1200, true, BOT_MODE_NONE)
        
        -- Если на линии нет крипов и нет врагов — идем фармить лес по оптимальному маршруту
        if (nearby_creeps == nil or #nearby_creeps == 0) and (nearby_enemy_heroes == nil or #nearby_enemy_heroes == 0) then
            if _G.last_jungle_camp_idx == nil then _G.last_jungle_camp_idx = {} end
            local c_idx = _G.last_jungle_camp_idx[bot_id] or 1
            
            local team_camps = JUNGLE_CAMPS[team]
            if team_camps ~= nil and #team_camps > 0 then
                local target_camp = team_camps[c_idx]
                local dist = GetDistance(bot_loc, target_camp)
                
                if dist > 150 then
                    bot:Action_MoveToLocation(Vector(target_camp.x, target_camp.y, target_camp.z))
                    print(string.format("[JUNGLE_PATH] Core %s (pos %d) farming jungle camp #%d | Dist: %.0f",
                        bot:GetUnitName(), pos, c_idx, dist))
                    return
                else
                    -- Мы пришли на спот! Атакуем нейтралов
                    local neutrals = bot:GetNearbyCreeps(600, true)
                    if neutrals ~= nil and #neutrals > 0 then
                        bot:Action_AttackUnit(neutrals[1], true)
                        return
                    else
                        -- Спот пустой — переходим к следующему лагерю
                        _G.last_jungle_camp_idx[bot_id] = (c_idx % #team_camps) + 1
                        print(string.format("[JUNGLE_PATH] Camp #%d empty, moving to camp #%d", c_idx, _G.last_jungle_camp_idx[bot_id]))
                    end
                end
            end
        end
    end

    -- ==================== [25/22] PERFECT SPELL COMBO SYNCHRONIZATION (Zero-frame Trap) ====================
    if not bot:IsCastingAbility() then
        local target_enemies = bot:GetNearbyHeroes(800, true, BOT_MODE_NONE)
        if target_enemies ~= nil and #target_enemies > 0 and target_enemies[1]:IsAlive() then
            local enemy = target_enemies[1]
            -- Zero-frame прокаст для Лины: сначала стан, затем Dragon Slave
            if bot:GetUnitName() == "npc_dota_hero_lina" then
                local lsa = bot:GetAbilityByName("lina_light_strike_array")
                local slave = bot:GetAbilityByName("lina_dragon_slave")
                
                if lsa and lsa:IsFullyCastable() then
                    bot:Action_UseAbilityOnLocation(lsa, enemy:GetLocation())
                    print("[COMBO] LINA casted Light Strike Array!")
                    return
                elseif slave and slave:IsFullyCastable() and enemy:HasModifier("modifier_stunned") then
                    bot:Action_UseAbilityOnLocation(slave, enemy:GetLocation())
                    print("[COMBO] LINA sync casted Dragon Slave on stunned target!")
                    return
                end
            end
        end
    end

    -- ==================== [26/22] PERFECT BLINK INITIATION (Прыжок с блинка при скоплении врагов) ====================
    local blink_slot = bot:FindItemSlot("item_blink")
    if blink_slot ~= nil and blink_slot >= 0 and blink_slot <= 5 then
        local blink_item = bot:GetItemInSlot(blink_slot)
        if blink_item and blink_item:IsFullyCastable() then
            -- Ищем группу врагов в радиусе Blink (1200) + Ravage/Call (400)
            local visible_enemies = bot:GetNearbyHeroes(1500, true, BOT_MODE_NONE)
            if visible_enemies ~= nil and #visible_enemies >= 3 then
                -- Вычисляем геометрический центр группы врагов
                local sum_x = 0
                local sum_y = 0
                local active_count = 0
                for _, enemy in ipairs(visible_enemies) do
                    if enemy ~= nil and enemy:IsAlive() then
                        local loc = enemy:GetLocation()
                        sum_x = sum_x + loc.x
                        sum_y = sum_y + loc.y
                        active_count = active_count + 1
                    end
                end
                
                if active_count >= 3 then
                    local center = Vector(sum_x / active_count, sum_y / active_count, 128)
                    -- Прыгаем в центр скопления
                    bot:Action_UseAbilityOnLocation(blink_item, center)
                    print(string.format("[BLINK_INIT] Hero %s BLINK INITIATION into center of %d enemies!", bot:GetUnitName(), active_count))
                    
                    -- Сразу прожимаем Ravage или Berserker's Call в следующем кадре
                    local ult = bot:GetAbilityInSlot(5)
                    if ult and ult:IsFullyCastable() then
                        bot:Action_UseAbility(ult)
                        print("[BLINK_INIT] Pop ultimate after blink!")
                    end
                    return
                end
            end
        end
    end

    -- ==================== [27/22] SMART AEGIS REINCARNATION POSITIONING (Защита креста Аегиса) ====================
    if _G.aegis_holder_reincarnating == nil then _G.aegis_holder_reincarnating = false end
    if _G.aegis_reincarnate_loc == nil then _G.aegis_reincarnate_loc = nil end

    -- Отслеживаем смерть союзника с Аегисом
    for pid = 0, 4 do
        local member = GetTeamMember(pid + 1)
        if member ~= nil and not member:IsAlive() and member:HasModifier("modifier_item_aegis") then
            _G.aegis_holder_reincarnating = true
            _G.aegis_reincarnate_loc = member:GetLocation()
            _G.aegis_reincarnate_time = now
        end
    end

    if _G.aegis_holder_reincarnating and _G.aegis_reincarnate_loc ~= nil then
        if (now - _G.aegis_reincarnate_time) > 5.0 then
            _G.aegis_holder_reincarnating = false
            _G.aegis_reincarnate_loc = nil
        else
            -- Все живые союзники стягиваются к месту перерождения для прикрытия и контр-атаки
            local dist = GetDistance(bot_loc, _G.aegis_reincarnate_loc)
            if dist > 300 and dist < 2000 then
                bot:Action_MoveToLocation(_G.aegis_reincarnate_loc)
                print(string.format("[AEGIS_PROTECT] Hero %s grouping up around reincarnating ally!", bot:GetUnitName()))
                return
            end
        end
    end

    -- ==================== [28/22] SMART ENEMY COOLDOWN TRACKER (Драка по КД вражеских ультов) ====================
    if _G.enemy_ult_cooldowns == nil then _G.enemy_ult_cooldowns = {} end
    local visible_enemies = bot:GetNearbyHeroes(1600, true, BOT_MODE_NONE)
    if visible_enemies ~= nil then
        for _, enemy in ipairs(visible_enemies) do
            if enemy ~= nil and enemy:IsAlive() then
                -- Если враг только что скастовал большой ульт (например, Ravage Tidehunter)
                if enemy:IsCastingAbility() and (enemy:GetUnitName() == "npc_dota_hero_tidehunter" or enemy:GetUnitName() == "npc_dota_hero_enigma") then
                    _G.enemy_ult_cooldowns[enemy:GetUnitName()] = now + 150 -- Ставим КД 150 секунд
                    print(string.format("[COOLDOWN_TRACK] Tracked enemy %s popped ultimate! Cooldown active for 150s.", enemy:GetUnitName()))
                end
            end
        end
    end

    -- ==================== [29/22] ADVANCED JUKE PATHFINDER (Мансование в лесах) ====================
    if hp < 0.20 and bot:WasRecentlyDamagedByAnyHero(1.5) then
        -- Нас зажали! Бежим в ближайшие деревья для сброса вижна
        local trees = GetNearbyTrees(bot, 1000)
        if trees ~= nil and #trees > 0 then
            -- Ищем слепую зону
            local juke_tree = GetTreeLocation(trees[1])
            bot:Action_MoveToLocation(juke_tree)
            
            -- Если есть Танго или топорик — прорубаем проход в слепую зону
            local quelling = bot:FindItemSlot("item_quelling_blade")
            if quelling ~= nil and quelling >= 0 then
                local q_item = bot:GetItemInSlot(quelling)
                if q_item and q_item:IsFullyCastable() then
                    bot:Action_UseAbilityOnTree(q_item, trees[1])
                    print(string.format("[JUKE] Hero %s cut tree at (%.0f, %.0f) to escape into Fog of War!",
                        bot:GetUnitName(), juke_tree.x, juke_tree.y))
                    return
                end
            end
    -- ==================== [30/22] HIGH GROUND DEFENSE DIRECTOR (Глухая ХГ-оборона) ====================
    local opposing = (team == 2) and 3 or 2
    local ancient = GetAncient(team)
    local t3_under_siege = false
    local siege_tower_loc = nil
    
    local t3_towers = {
        GetTower(team, TOWER_TOP_3),
        GetTower(team, TOWER_MID_3),
        GetTower(team, TOWER_BOT_3)
    }
    for _, t3 in ipairs(t3_towers) do
        if t3 ~= nil and t3:IsAlive() then
            local attackers = t3:GetNearbyHeroes(1400, true, BOT_MODE_NONE)
            if attackers ~= nil and #attackers > 0 then
                t3_under_siege = true
                siege_tower_loc = t3:GetLocation()
                break
            end
        end
    end
    
    if t3_under_siege and siege_tower_loc ~= nil then
        -- Мы под осадой на ХГ!
        local dist_to_siege = GetDistance(bot_loc, siege_tower_loc)
        
        if pos == 4 or pos == 5 then
            -- Саппорты стоят глубоко сзади в зоне безопасности бараков / фонтана
            local safe_back_pos = siege_tower_loc - Vector(team == 2 and 600 or -600, 0, 0)
            if dist_to_siege < 500 then
                bot:Action_MoveToLocation(safe_back_pos)
                print(string.format("[HG_DEFENSE] Support %s hugging safe high ground backline!", bot:GetUnitName()))
                return
            end
        elseif pos == 1 or pos == 2 then
            -- Коры стоят строго под защитой Т3 вышки и не лезут вперед в одиночку
            local tower_hug_pos = siege_tower_loc - Vector(team == 2 and 250 or -250, 0, 0)
            if dist_to_siege > 800 then
                bot:Action_MoveToLocation(tower_hug_pos)
                print(string.format("[HG_DEFENSE] Core %s hugging T3 tower for protection!", bot:GetUnitName()))
                return
            end
        elseif pos == 3 then
            -- Оффлейнер инициирует строго тогда, когда враг бьет вышку
            local enemy_attackers = bot:GetNearbyHeroes(700, true, BOT_MODE_NONE)
            if enemy_attackers ~= nil and #enemy_attackers > 0 then
                local initiator_spell = bot:GetAbilityInSlot(5) -- Ravage / Call
                if initiator_spell and initiator_spell:IsFullyCastable() then
                    bot:Action_UseAbility(initiator_spell)
                    print("[HG_DEFENSE] Offlane popped counter-init ultimate under T3 tower!")
                    return
                end
            end
        end
    end

    -- ==================== [31/22] SMART TELEPORT ESCAPE (Моментальный сэйв-ТР на базу) ====================
    if hp < 0.12 and bot:WasRecentlyDamagedByAnyHero(1.0) then
        local enemy_attackers = bot:GetNearbyHeroes(800, true, BOT_MODE_NONE)
        if enemy_attackers ~= nil and #enemy_attackers >= 2 then
            -- Нас зажали и путей к отступлению нет! Мгновенно прожимаем ТП на базу
            local tp_slot = bot:FindItemSlot("item_tpscroll")
            if tp_slot ~= nil and tp_slot >= 0 and tp_slot <= 5 then
                local tp_item = bot:GetItemInSlot(tp_slot)
                if tp_item and tp_item:IsFullyCastable() then
                    local base_fountain = (team == 2) and Vector(-7200, -6700, 384) or Vector(7200, 6700, 384)
                    bot:Action_UseAbilityOnLocation(tp_item, base_fountain)
                    print(string.format("[TP_ESCAPE] Hero %s under critical focus! Initiated emergency TP to base!", bot:GetUnitName()))
                    return
                end
            end
        end
    end

    -- ==================== [32/22] DYNAMIC WARD BLOCK DEWARDING (Девардинг заблокированных кемпов) ====================
    if (pos == 4 or pos == 5) and now > 120 then
        -- Если наш лесной лагерь заблокирован вражеским вардом
        for idx, camp_pos in ipairs(JUNGLE_CAMPS[team]) do
            local v_camp = Vector(camp_pos.x, camp_pos.y, camp_pos.z)
            -- Проверяем спавн крипов: если спот пустой, но время перевалило за XX:00
            local sec = now % 60
            if sec > 2 and sec < 8 then
                local neutrals = bot:GetNearbyCreeps(500, true)
                if neutrals == nil or #neutrals == 0 then
                    -- Спот, скорее всего, заблокирован! Ставим Sentry для девардинга
                    local sentry = bot:FindItemSlot("item_ward_sentry")
                    if sentry ~= nil and sentry >= 0 and sentry <= 5 then
                        local sentry_item = bot:GetItemInSlot(sentry)
                        if sentry_item and sentry_item:IsFullyCastable() then
                            local dist = GetDistance(bot_loc, v_camp)
                            if dist > 300 then
                                bot:Action_MoveToLocation(v_camp)
                                return
                            else
                                bot:Action_UseAbilityOnLocation(sentry_item, v_camp)
                                print(string.format("[WARD_DEBLOCK] Support %s deblocking camp #%d at (%.0f, %.0f)!", bot:GetUnitName(), idx, v_camp.x, v_camp.y))
                                return
                            end
                        end
                    end
                end
            end
        end
    end

    -- ==================== [33/22] PERFECT MANTA SILENCE PURGE (Мгновенный сброс безмолвия / дебаффов) ====================
    if bot:HasModifier("modifier_silence") or bot:HasModifier("modifier_slardar_corrosive_haze") or bot:HasModifier("modifier_bounty_hunter_track") then
        -- На нас висит критический дебафф/сайлэнс! Сбрасываем его Мантой или BKB
        local manta = bot:FindItemSlot("item_manta")
        if manta ~= nil and manta >= 0 and manta <= 5 then
            local manta_item = bot:GetItemInSlot(manta)
            if manta_item and manta_item:IsFullyCastable() then
                bot:Action_UseAbility(manta_item)
                print(string.format("[PURGE] ID:%d | Used Manta Style to purge negative debuffs!", bot_id))
                return
            end
        end
    end

    -- ==================== [34/22] SMART AEGIS RECLAIM SAVE (Сэйв союзника после реинкарнации) ====================
    if _G.aegis_holder_reincarnating and _G.aegis_reincarnate_loc ~= nil then
        -- Если мы саппорт и стоим рядом с крестом союзника
        local dist = GetDistance(bot_loc, _G.aegis_reincarnate_loc)
        if (pos == 4 or pos == 5) and dist < 700 then
            -- Готовим Force Staff на точку реинкарнации
            local force = bot:FindItemSlot("item_force_staff")
            if force ~= nil and force >= 0 and force <= 5 then
                local force_item = bot:GetItemInSlot(force)
                if force_item and force_item:IsFullyCastable() then
                    -- Находим переродившегося союзника
                    local nearby_allies = bot:GetNearbyHeroes(700, false, BOT_MODE_NONE)
                    if nearby_allies ~= nil then
                        for _, ally in ipairs(nearby_allies) do
                            if ally ~= nil and ally:IsAlive() and ally:GetHealth() < (ally:GetMaxHealth() * 0.4) then
                                bot:Action_UseAbilityOnEntity(force_item, ally)
                                print(string.format("[AEGIS_SAVE] Support %s used Force Staff to push ally %s to safety!", bot:GetUnitName(), ally:GetUnitName()))
                                return
                            end
                        end
                    end
                end
            end
        end
    end

    -- ==================== [35/22] SMART ENEMY MANA BAITING (Ложные движения для байта спеллов врага) ====================
    if now < 600 and not bot:IsCastingAbility() then
        local enemy_mid = bot:GetNearbyHeroes(800, true, BOT_MODE_NONE)
        if enemy_mid ~= nil and #enemy_mid > 0 then
            local target = enemy_mid[1]
            -- Делаем ложный выпад вперед на 0.2 сек, затем отступаем, провоцируя врага дать спелл в пустоту
            if _G.bait_movement_time == nil then _G.bait_movement_time = 0 end
            if now - _G.bait_movement_time > 15 then
                local bait_loc = bot_loc + (target:GetLocation() - bot_loc) * 0.4
                bot:Action_MoveToLocation(bait_loc)
                _G.bait_movement_time = now
                print(string.format("[BAITING] %s initiated fake forward movement to bait enemy spell!", bot:GetUnitName()))
                return
            end
        end
    end

    -- ==================== [36/22] PERFECT LOTUS SPHERE REFLECT BAIT (Байт с Лотусом на ультимейты) ====================
    local lotus = bot:FindItemSlot("item_lotus_orb")
    if lotus ~= nil and lotus >= 0 and lotus <= 5 then
        local lotus_item = bot:GetItemInSlot(lotus)
        if lotus_item and lotus_item:IsFullyCastable() then
            local visible_enemies = bot:GetNearbyHeroes(800, true, BOT_MODE_NONE)
            if visible_enemies ~= nil and #visible_enemies > 0 then
                for _, enemy in ipairs(visible_enemies) do
                    -- Если враг — Лина или Лион (герои с направленными фатальными ультами)
                    if enemy:GetUnitName() == "npc_dota_hero_lina" or enemy:GetUnitName() == "npc_dota_hero_lion" then
                        -- Прожимаем Лотус перед тем как подойти ближе, чтобы отразить спелл!
                        bot:Action_UseAbilityOnEntity(lotus_item, bot)
                        print(string.format("[LOTUS_BAIT] Hero %s popped Lotus Orb to bait enemy fatal ultimate!", bot:GetUnitName()))
                        return
                    end
                end
            end
        end
    end
    -- ==================== [42/22] WOMBO COMBO COORDINATOR (Цепочки ультимейтов) ====================
    if _G.active_ultimate_cast == nil then _G.active_ultimate_cast = {} end
    if _G.active_ultimate_time == nil then _G.active_ultimate_time = 0 end
    
    if now - _G.active_ultimate_time > 4.0 then
        _G.active_ultimate_cast = {}
    end
    
    local ult = bot:GetAbilityInSlot(5)
    if ult and ult:IsFullyCastable() then
        local ult_name = ult:GetName()
        local another_ult_active = false
        for pid, u_name in pairs(_G.active_ultimate_cast) do
            if pid ~= bot_id then
                another_ult_active = true
                break
            end
        end
        
        if another_ult_active then
            if ult_name == "tidehunter_ravage" or ult_name == "earthshaker_echo_slam" or ult_name == "enigma_black_hole" then
                print(string.format("[WOMBO_COMBO] Hero %s holding ultimate %s to prevent overlap with ally!", bot:GetUnitName(), ult_name))
                return
            end
        else
            if bot:IsCastingAbility() and (ult_name == "tidehunter_ravage" or ult_name == "enigma_black_hole" or ult_name == "magnataur_reverse_polarity") then
                _G.active_ultimate_cast[bot_id] = ult_name
                _G.active_ultimate_time = now
                print(string.format("[WOMBO_COMBO] Hero %s popped primary initiator ultimate: %s!", bot:GetUnitName(), ult_name))
            end
        end
    end

    -- ==================== [43/22] PRO GAMER CHAT BANTER (Киберспортивный чат и токсичность) ====================
    if _G.last_chat_time == nil then _G.last_chat_time = 0 end
    
    if now - _G.last_chat_time > 30 then
        local opposing = (team == 2) and 3 or 2
        local enemy_ids = GetTeamPlayers(opposing)
        for _, eid in ipairs(enemy_ids) do
            if not IsHeroAlive(eid) then
                if _G.last_kill_chat == nil then _G.last_kill_chat = {} end
                if _G.last_kill_chat[eid] == nil or (now - _G.last_kill_chat[eid]) > 180 then
                    _G.last_kill_chat[eid] = now
                    _G.last_chat_time = now
                    
                    local toxic_phrases = {
                        "ez lane", "easy game", "купи руки", "ластхит уровня рекрут", 
                        "uninstall dota please", "?", "типичный пабчик", "удаляй доту", "ez",
                        "сходи пофарми лес", "БУРМАЛДА", "БУРМАЛДА!", "БУРМАЛДА!!!"
                    }
                    local phrase = toxic_phrases[(bot_id + math.floor(now)) % #toxic_phrases + 1]
                    
                    bot:ActionImmediate_Chat(phrase, true)
                    bot:ActionImmediate_Chat("?", true)
                    print(string.format("[CHAT_BANTER] Trolled enemy player %d with phrase: %s", eid, phrase))
                end
            end
        end
        
        if bot:HasModifier("modifier_item_lotus_orb_active") or bot:HasModifier("modifier_item_glimmer_cape") then
            if _G.last_save_chat == nil or now - _G.last_save_chat > 60 then
                _G.last_save_chat = now
                _G.last_chat_time = now
                
                local thanks_phrases = {
                    "ty support", "spasibo", "best support ever", "лучший саппорт в мире!", "ty", "gj"
                }
                local phrase = thanks_phrases[(bot_id + math.floor(now)) % #thanks_phrases + 1]
                bot:ActionImmediate_Chat(phrase, false)
                print(string.format("[CHAT_BANTER] Appreciated support save: %s", phrase))
            end
        end
    end

    -- ==================== [44/22] STRATEGIC NETWORTH AGGRESSION TUNING (Адаптивная агрессия по золоту) ====================
    if _G.global_aggression_tier == nil then _G.global_aggression_tier = 3 end
    if _G.networth_last_check == nil then _G.networth_last_check = 0 end
    
    if now - _G.networth_last_check > 15 then
        _G.networth_last_check = now
        
        local our_total_gold = 0
        for pid = 0, 4 do
            local member = GetTeamMember(pid + 1)
            if member ~= nil then
                our_total_gold = our_total_gold + member:GetNetWorth()
            end
        end
        
        local enemy_est_gold = 5 * (now / 60) * 450
        local advantage = our_total_gold - enemy_est_gold
        
        if advantage > 8000 then
            _G.global_aggression_tier = 5
        elseif advantage > 3000 then
            _G.global_aggression_tier = 4
        elseif advantage < -8000 then
            _G.global_aggression_tier = 1
        elseif advantage < -3000 then
            _G.global_aggression_tier = 2
        else
            _G.global_aggression_tier = 3
        end
    end

    -- ==================== [37/22] REAL-TIME PARAMETER SELF-TUNING AI (Адаптивное самообучение в матче) ====================
    if _G.bot_adaptive_delay == nil then _G.bot_adaptive_delay = {} end
    if _G.bot_aggression_factor == nil then _G.bot_aggression_factor = {} end
    
    if _G.bot_adaptive_delay[bot_id] == nil then
        _G.bot_adaptive_delay[bot_id] = 0.05
    end
    if _G.bot_aggression_factor[bot_id] == nil then
        _G.bot_aggression_factor[bot_id] = 1.0 + ((_G.global_aggression_tier or 3) - 3) * 0.15
    end
    
    -- Динамическая самонастройка параметров на основе здоровья и смертей
    local deaths_count = GetHeroDeaths(bot_id)
    if _G.last_recorded_deaths == nil then _G.last_recorded_deaths = {} end
    local prev_deaths = _G.last_recorded_deaths[bot_id] or 0
    
    if deaths_count > prev_deaths then
        -- Мы умерли! Обучаемся: снижаем агрессию и ускоряем реакцию доджа
        _G.last_recorded_deaths[bot_id] = deaths_count
        _G.bot_aggression_factor[bot_id] = math.max(0.6, _G.bot_aggression_factor[bot_id] - 0.15)
        _G.bot_adaptive_delay[bot_id] = math.max(0.02, _G.bot_adaptive_delay[bot_id] - 0.01) -- ускоряем додж на 10мс
        print(string.format("[SELF_TUNING] Bot ID:%d DIED! Adapting: Aggression decreased to %.2f | Dodge delay optimized to %.0fms!", 
            bot_id, _G.bot_aggression_factor[bot_id], _G.bot_adaptive_delay[bot_id] * 1000))
    end
    
    -- Если бот успешно делает стрики (киллы растут), увеличиваем агрессию
    local kills_count = GetHeroKills(bot_id)
    if _G.last_recorded_kills == nil then _G.last_recorded_kills = {} end
    local prev_kills = _G.last_recorded_kills[bot_id] or 0
    if kills_count > prev_kills then
        _G.last_recorded_kills[bot_id] = kills_count
        _G.bot_aggression_factor[bot_id] = math.min(1.5, _G.bot_aggression_factor[bot_id] + 0.1) -- становимся увереннее
        print(string.format("[SELF_TUNING] Bot ID:%d KILLED enemy! Adapting: Aggression increased to %.2f!", 
            bot_id, _G.bot_aggression_factor[bot_id]))
    end

    -- ==================== [40/22] BLINK-INTO-FOG EMERGENCY JUKE (Блинк-эскейп и сэйв-ТР) ====================
    if hp < 0.35 and bot:WasRecentlyDamagedByAnyHero(1.5) then
        local blink_slot = bot:FindItemSlot("item_blink") or bot:FindItemSlot("item_overwhelming_blink") or bot:FindItemSlot("item_swift_blink") or bot:FindItemSlot("item_arcane_blink")
        
        if blink_slot ~= nil and blink_slot >= 0 and blink_slot <= 5 then
            local blink_item = bot:GetItemInSlot(blink_slot)
            if blink_item ~= nil and blink_item:IsFullyCastable() then
                local trees = GetNearbyTrees(bot, 1150)
                local safe_juke_loc = nil
                
                if trees ~= nil and #trees > 0 then
                    local enemy_heroes = bot:GetNearbyHeroes(1000, true, BOT_MODE_NONE)
                    local enemy_center = bot_loc
                    if enemy_heroes ~= nil and #enemy_heroes > 0 then
                        local sx, sy = 0, 0
                        for _, enemy in ipairs(enemy_heroes) do
                            local el = enemy:GetLocation()
                            sx = sx + el.x
                            sy = sy + el.y
                        end
                        enemy_center = Vector(sx / #enemy_heroes, sy / #enemy_heroes, 128)
                    end
                    
                    local max_dist_from_enemy = -1
                    for i = 1, math.min(#trees, 12) do
                        local t_loc = GetTreeLocation(trees[i])
                        local d_from_enemy = GetDistance(t_loc, enemy_center)
                        if d_from_enemy > max_dist_from_enemy then
                            max_dist_from_enemy = d_from_enemy
                            safe_juke_loc = t_loc
                        end
                    end
                end
                
                if safe_juke_loc == nil then
                    local base_fountain = (team == 2) and Vector(-7200, -6700, 384) or Vector(7200, 6700, 384)
                    local dir = (base_fountain - bot_loc)
                    local len = math.sqrt(dir.x^2 + dir.y^2)
                    safe_juke_loc = bot_loc + Vector((dir.x / len) * 1150, (dir.y / len) * 1150, 0)
                end
                
                bot:Action_UseAbilityOnLocation(blink_item, safe_juke_loc)
                print(string.format("[EMERGENCY_BLINK] Hero %s pop EMERGENCY BLINK into forest camp! HP: %.1f%%", bot:GetUnitName(), hp * 100))
                
                local tp_slot = bot:FindItemSlot("item_tpscroll")
                if tp_slot ~= nil and tp_slot >= 0 and tp_slot <= 5 then
                    local tp_item = bot:GetItemInSlot(tp_slot)
                    if tp_item ~= nil and tp_item:IsFullyCastable() then
                        local base_fountain = (team == 2) and Vector(-7200, -6700, 384) or Vector(7200, 6700, 384)
                        bot:Action_UseAbilityOnLocation(tp_item, base_fountain)
                        print(string.format("[EMERGENCY_BLINK] Hero %s successfully chained safe TP to fountain!", bot:GetUnitName()))
                        return
                    end
                end
                return
            end
        end
    end

    -- ==================== ML micro-movement model prediction ====================
    local nearest_creeps = get_nearest_creeps(bot)
    if #nearest_creeps == 0 then
        return
    end

    local c = {}
    for i = 1, 5 do
        if nearest_creeps[i] then
            local cl = nearest_creeps[i]:GetLocation()
            local chp = 0.0
            if nearest_creeps[i]:GetMaxHealth() > 0 then chp = nearest_creeps[i]:GetHealth() / nearest_creeps[i]:GetMaxHealth() end
            c[i] = {
                dx = cl.x - bot_loc.x,
                dy = cl.y - bot_loc.y,
                hp = chp,
                dist = GetUnitToUnitDistance(bot, nearest_creeps[i]),
                team = nearest_creeps[i]:GetTeam()
            }
        else
            c[i] = { dx = 0, dy = 0, hp = 0, dist = 0, team = 0 }
        end
    end

    local dx, dy = 0.0, 0.0
    
    if pos == 1 then
        dx = predict_mx_pos1(hp, mp, c[1].dx, c[1].dy, c[1].hp, c[1].dist, c[1].team, c[2].dx, c[2].dy, c[2].hp, c[2].dist, c[2].team, c[3].dx, c[3].dy, c[3].hp, c[3].dist, c[3].team, c[4].dx, c[4].dy, c[4].hp, c[4].dist, c[4].team, c[5].dx, c[5].dy, c[5].hp, c[5].dist, c[5].team)
        dy = predict_my_pos1(hp, mp, c[1].dx, c[1].dy, c[1].hp, c[1].dist, c[1].team, c[2].dx, c[2].dy, c[2].hp, c[2].dist, c[2].team, c[3].dx, c[3].dy, c[3].hp, c[3].dist, c[3].team, c[4].dx, c[4].dy, c[4].hp, c[4].dist, c[4].team, c[5].dx, c[5].dy, c[5].hp, c[5].dist, c[5].team)
    elseif pos == 2 then
        dx = predict_mx_pos2(hp, mp, c[1].dx, c[1].dy, c[1].hp, c[1].dist, c[1].team, c[2].dx, c[2].dy, c[2].hp, c[2].dist, c[2].team, c[3].dx, c[3].dy, c[3].hp, c[3].dist, c[3].team, c[4].dx, c[4].dy, c[4].hp, c[4].dist, c[4].team, c[5].dx, c[5].dy, c[5].hp, c[5].dist, c[5].team)
        dy = predict_my_pos2(hp, mp, c[1].dx, c[1].dy, c[1].hp, c[1].dist, c[1].team, c[2].dx, c[2].dy, c[2].hp, c[2].dist, c[2].team, c[3].dx, c[3].dy, c[3].hp, c[3].dist, c[3].team, c[4].dx, c[4].dy, c[4].hp, c[4].dist, c[4].team, c[5].dx, c[5].dy, c[5].hp, c[5].dist, c[5].team)
    elseif pos == 3 then
        dx = predict_mx_pos3(hp, mp, c[1].dx, c[1].dy, c[1].hp, c[1].dist, c[1].team, c[2].dx, c[2].dy, c[2].hp, c[2].dist, c[2].team, c[3].dx, c[3].dy, c[3].hp, c[3].dist, c[3].team, c[4].dx, c[4].dy, c[4].hp, c[4].dist, c[4].team, c[5].dx, c[5].dy, c[5].hp, c[5].dist, c[5].team)
        dy = predict_my_pos3(hp, mp, c[1].dx, c[1].dy, c[1].hp, c[1].dist, c[1].team, c[2].dx, c[2].dy, c[2].hp, c[2].dist, c[2].team, c[3].dx, c[3].dy, c[3].hp, c[3].dist, c[3].team, c[4].dx, c[4].dy, c[4].hp, c[4].dist, c[4].team, c[5].dx, c[5].dy, c[5].hp, c[5].dist, c[5].team)
    elseif pos == 4 then
        dx = predict_mx_pos4(hp, mp, c[1].dx, c[1].dy, c[1].hp, c[1].dist, c[1].team, c[2].dx, c[2].dy, c[2].hp, c[2].dist, c[2].team, c[3].dx, c[3].dy, c[3].hp, c[3].dist, c[3].team, c[4].dx, c[4].dy, c[4].hp, c[4].dist, c[4].team, c[5].dx, c[5].dy, c[5].hp, c[5].dist, c[5].team)
        dy = predict_my_pos4(hp, mp, c[1].dx, c[1].dy, c[1].hp, c[1].dist, c[1].team, c[2].dx, c[2].dy, c[2].hp, c[2].dist, c[2].team, c[3].dx, c[3].dy, c[3].hp, c[3].dist, c[3].team, c[4].dx, c[4].dy, c[4].hp, c[4].dist, c[4].team, c[5].dx, c[5].dy, c[5].hp, c[5].dist, c[5].team)
    else
        dx = predict_mx_pos5(hp, mp, c[1].dx, c[1].dy, c[1].hp, c[1].dist, c[1].team, c[2].dx, c[2].dy, c[2].hp, c[2].dist, c[2].team, c[3].dx, c[3].dy, c[3].hp, c[3].dist, c[3].team, c[4].dx, c[4].dy, c[4].hp, c[4].dist, c[4].team, c[5].dx, c[5].dy, c[5].hp, c[5].dist, c[5].team)
        dy = predict_my_pos5(hp, mp, c[1].dx, c[1].dy, c[1].hp, c[1].dist, c[1].team, c[2].dx, c[2].dy, c[2].hp, c[2].dist, c[2].team, c[3].dx, c[3].dy, c[3].hp, c[3].dist, c[3].team, c[4].dx, c[4].dy, c[4].hp, c[4].dist, c[4].team, c[5].dx, c[5].dy, c[5].hp, c[5].dist, c[5].team)
    end

    local target = Vector(bot_loc.x + dx, bot_loc.y + dy, bot_loc.z)
    bot:Action_MoveToLocation(target)

    print(string.format("[BOT_STAT] ID:%d|HERO:%s|HP:%.2f|MP:%.2f|LOC:%.0f,%.0f|ACTION:ML_MOVE|TARGET_CREEPS:%d|LANE:%d",
        bot_id, bot:GetUnitName(), hp, mp, bot_loc.x, bot_loc.y, #nearest_creeps, bot:GetAssignedLane()))
end
""")
    
    # Write the complete file
    full_lua = "\n".join(lua_parts)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(full_lua)
        
    print(f"\n=== Dynamic 5-Position model export complete! ===")
    print(f"Total exported trees: {total_trees}")
    print(f"File size: {os.path.getsize(OUTPUT_PATH) / 1024:.1f} KB")

    # Copy to Dota 2 bots directory
    import shutil
    dota_bots_dir = r"C:\stea\steamapps\common\dota 2 beta\game\dota\scripts\vscripts\bots"
    
    if os.path.exists(dota_bots_dir):
        dst_path = os.path.join(dota_bots_dir, "bot_generic.lua")
        try:
            shutil.copy2(OUTPUT_PATH, dst_path)
            print(f"Successfully deployed bot_generic.lua directly to Dota 2 client: {dst_path}")
        except Exception as e:
            print(f"Error deploying bot_generic.lua: {e}")

if __name__ == "__main__":
    main()
