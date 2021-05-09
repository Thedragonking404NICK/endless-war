import time
import random
import asyncio

from ..static import cfg as ewcfg
from ..static import weapons as static_weapons
from ..static import hunting as hunt_static
from ..static import poi as poi_static
from ..static import status as se_static
from ..static import slimeoid as sl_static
from ..utils import core as ewutils, rolemgr as ewrolemgr
from ..utils import frontend as fe_utils
from ..utils import hunting as hunt_utils
from .. import wep as ewwep
from . import core as bknd_core
from . import item as bknd_item


from .user import EwUser
from .item import EwItem
from .market import EwMarket
from .player import EwPlayer
from .district import EwDistrict
from .slimeoid import EwSlimeoid
from .status import EwEnemyStatusEffect
from ..model.hunting import EwEnemyEffectContainer
from ..utils.frontend import EwResponseContainer

""" Enemy data model for database persistence """
class EwEnemy:
	id_enemy = 0
	id_server = -1

	combatant_type = "enemy"

	# The amount of slime an enemy has
	slimes = 0

	# The total amount of damage an enemy has sustained throughout its lifetime
	totaldamage = 0

	# The type of AI the enemy uses to select which players to attack
	ai = ""

	# The name of enemy shown in responses
	display_name = ""

	# Used to help identify enemies of the same type in a district
	identifier = ""

	# An enemy's level, which determines how much damage it does
	level = 0

	# An enemy's location
	poi = ""

	# Life state 0 = Dead, pending for deletion when it tries its next attack / action
	# Life state 1 = Alive / Activated raid boss
	# Life state 2 = Raid boss pending activation
	life_state = 0

	# Used to determine how much slime an enemy gets, what AI it uses, as well as what weapon it uses.
	enemytype = ""

	# The 'weapon' of an enemy
	attacktype = ""

	# An enemy's bleed storage
	bleed_storage = 0

	# Used for determining when a raid boss should be able to move between districts
	time_lastenter = 0

	# Used to determine how much slime an enemy started out with to create a 'health bar' ( current slime / initial slime )
	initialslimes = 0

	# Enemies despawn when this value is less than int(time.time())
	expiration_date = 0

	# Used by the 'defender' AI to determine who it should retaliate against
	id_target = -1

	# Used by raid bosses to determine when they should activate
	raidtimer = 0
	
	# Determines if an enemy should use its rare variant or not
	rare_status = 0
	
	# What kind of weather the enemy is suited to
	weathertype = 0

	# Sap armor
	#hardened_sap = 0
	
	# What faction the enemy belongs to
	faction = ""
	
	# What class the enemy belongs to
	enemyclass = ""
	
	# Tracks which user is associated with the enemy
	owner = -1

	# Coordinate used for enemies in Gankers Vs. Shamblers
	gvs_coord = ""
	
	# Various properties different enemies might have
	enemy_props = ""

	""" Load the enemy data from the database. """

	def __init__(self, id_enemy=None, id_server=None, enemytype=None):
		self.combatant_type = ewcfg.combatant_type_enemy
		self.enemy_props = {}

		query_suffix = ""

		if id_enemy != None:
			query_suffix = " WHERE id_enemy = '{}'".format(id_enemy)
		else:

			if id_server != None:
				query_suffix = " WHERE id_server = '{}'".format(id_server)
				if enemytype != None:
					query_suffix += " AND enemytype = '{}'".format(enemytype)

		if query_suffix != "":
			try:
				conn_info = bknd_core.databaseConnect()
				conn = conn_info.get('conn')
				cursor = conn.cursor()

				# Retrieve object
				cursor.execute(
					"SELECT {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {} FROM enemies{}".format(
						ewcfg.col_id_enemy,
						ewcfg.col_id_server,
						ewcfg.col_enemy_slimes,
						ewcfg.col_enemy_totaldamage,
						ewcfg.col_enemy_ai,
						ewcfg.col_enemy_type,
						ewcfg.col_enemy_attacktype,
						ewcfg.col_enemy_display_name,
						ewcfg.col_enemy_identifier,
						ewcfg.col_enemy_level,
						ewcfg.col_enemy_poi,
						ewcfg.col_enemy_life_state,
						ewcfg.col_enemy_bleed_storage,
						ewcfg.col_enemy_time_lastenter,
						ewcfg.col_enemy_initialslimes,
						ewcfg.col_enemy_expiration_date,
						ewcfg.col_enemy_id_target,
						ewcfg.col_enemy_raidtimer,
						ewcfg.col_enemy_rare_status,
						#ewcfg.col_enemy_hardened_sap,
						ewcfg.col_enemy_weathertype,
						ewcfg.col_faction,
						ewcfg.col_enemy_class,
						ewcfg.col_enemy_owner,
						ewcfg.col_enemy_gvs_coord,
						query_suffix
					))
				result = cursor.fetchone()

				if result != None:
					# Record found: apply the data to this object.
					self.id_enemy = result[0]
					self.id_server = result[1]
					self.slimes = result[2]
					self.totaldamage = result[3]
					self.ai = result[4]
					self.enemytype = result[5]
					self.attacktype = result[6]
					self.display_name = result[7]
					self.identifier = result[8]
					self.level = result[9]
					self.poi = result[10]
					self.life_state = result[11]
					self.bleed_storage = result[12]
					self.time_lastenter = result[13]
					self.initialslimes = result[14]
					self.expiration_date = result[15]
					self.id_target = result[16]
					self.raidtimer = result[17]
					self.rare_status = result[18]
					#self.hardened_sap = result[19]
					self.weathertype = result[19]
					self.faction = result[20]
					self.enemyclass = result[21]
					self.owner = result[22]
					self.gvs_coord = result[23]

					# Retrieve additional properties
					cursor.execute("SELECT {}, {} FROM enemies_prop WHERE id_enemy = %s".format(
						ewcfg.col_name,
						ewcfg.col_value
					), (
						self.id_enemy,
					))

					for row in cursor:
						# this try catch is only necessary as long as extraneous props exist in the table
						try:
							self.enemy_props[row[0]] = row[1]
						except:
							ewutils.logMsg("extraneous enemies_prop row detected.")

			finally:
				# Clean up the database handles.
				cursor.close()
				bknd_core.databaseClose(conn_info)

	""" Save enemy data object to the database. """

	def persist(self):
		try:
			conn_info = bknd_core.databaseConnect()
			conn = conn_info.get('conn')
			cursor = conn.cursor()

			# Save the object.
			cursor.execute(
				"REPLACE INTO enemies({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)".format(
					ewcfg.col_id_enemy,
					ewcfg.col_id_server,
					ewcfg.col_enemy_slimes,
					ewcfg.col_enemy_totaldamage,
					ewcfg.col_enemy_ai,
					ewcfg.col_enemy_type,
					ewcfg.col_enemy_attacktype,
					ewcfg.col_enemy_display_name,
					ewcfg.col_enemy_identifier,
					ewcfg.col_enemy_level,
					ewcfg.col_enemy_poi,
					ewcfg.col_enemy_life_state,
					ewcfg.col_enemy_bleed_storage,
					ewcfg.col_enemy_time_lastenter,
					ewcfg.col_enemy_initialslimes,
					ewcfg.col_enemy_expiration_date,
					ewcfg.col_enemy_id_target,
					ewcfg.col_enemy_raidtimer,
					ewcfg.col_enemy_rare_status,
					#ewcfg.col_enemy_hardened_sap,
					ewcfg.col_enemy_weathertype,
					ewcfg.col_faction,
					ewcfg.col_enemy_class,
					ewcfg.col_enemy_owner,
					ewcfg.col_enemy_gvs_coord
				), (
					self.id_enemy,
					self.id_server,
					self.slimes,
					self.totaldamage,
					self.ai,
					self.enemytype,
					self.attacktype,
					self.display_name,
					self.identifier,
					self.level,
					self.poi,
					self.life_state,
					self.bleed_storage,
					self.time_lastenter,
					self.initialslimes,
					self.expiration_date,
					self.id_target,
					self.raidtimer,
					self.rare_status,
					#self.hardened_sap,
					self.weathertype,
					self.faction,
					self.enemyclass,
					self.owner,
					self.gvs_coord,
				))
			
			# If the enemy doesn't have an ID assigned yet, have the cursor give us the proper ID.
			if self.id_enemy == 0:
				used_enemy_id = cursor.lastrowid
				#print('used new enemy id')
			else:
				used_enemy_id = self.id_enemy
				#print('used existing enemy id')
		
			# Remove all existing property rows.
			cursor.execute("DELETE FROM enemies_prop WHERE {} = %s".format(
				ewcfg.col_id_enemy
			), (
				used_enemy_id,
			))
			
			if self.enemy_props != None:
				for name in self.enemy_props:
					cursor.execute("INSERT INTO enemies_prop({}, {}, {}) VALUES(%s, %s, %s)".format(
						ewcfg.col_id_enemy,
						ewcfg.col_name,
						ewcfg.col_value
					), (
						used_enemy_id,
						name,
						self.enemy_props[name]
					))

			conn.commit()
		finally:
			# Clean up the database handles.
			cursor.close()
			bknd_core.databaseClose(conn_info)

	# Function that enemies use to attack or otherwise interact with players.
	async def kill(self):

		client = ewutils.get_client()

		last_messages = []
		should_post_resp_cont = True

		enemy_data = self

		time_now = int(time.time())
		resp_cont = EwResponseContainer(id_server=enemy_data.id_server)
		district_data = EwDistrict(district=enemy_data.poi, id_server=enemy_data.id_server)
		market_data = EwMarket(id_server=enemy_data.id_server)
		ch_name = poi_static.id_to_poi.get(enemy_data.poi).channel

		target_data = None
		target_player = None
		target_slimeoid = None

		used_attacktype = None

		# Get target's info based on its AI.

		if enemy_data.ai == ewcfg.enemy_ai_coward:
			users = bknd_core.execute_sql_query(
				"SELECT {id_user}, {life_state} FROM users WHERE {poi} = %s AND {id_server} = %s AND NOT ({life_state} = {life_state_corpse} OR {life_state} = {life_state_kingpin})".format(
					id_user=ewcfg.col_id_user,
					life_state=ewcfg.col_life_state,
					poi=ewcfg.col_poi,
					id_server=ewcfg.col_id_server,
					life_state_corpse=ewcfg.life_state_corpse,
					life_state_kingpin=ewcfg.life_state_kingpin,
				), (
					enemy_data.poi,
					enemy_data.id_server
				))
			if len(users) > 0:
				if random.randrange(100) > 95:
					response = random.choice(ewcfg.coward_responses)
					response = response.format(enemy_data.display_name, enemy_data.display_name)
					resp_cont.add_channel_response(ch_name, response)
					resp_cont.format_channel_response(ch_name, enemy_data)
					return resp_cont
					
					
		if enemy_data.ai == ewcfg.enemy_ai_sandbag:
			target_data = None
		else:
			target_data, group_attack = get_target_by_ai(enemy_data)

		if check_raidboss_countdown(enemy_data) and enemy_data.life_state == ewcfg.enemy_lifestate_unactivated:
			# Raid boss has activated!
			response = "*The ground quakes beneath your feet as slime begins to pool into one hulking, solidified mass...*" \
					   "\n{} **{} has arrived! It's level {} and has {} slime!** {}\n".format(
				ewcfg.emote_megaslime,
				enemy_data.display_name,
				enemy_data.level,
				enemy_data.slimes,
				ewcfg.emote_megaslime
			)
			resp_cont.add_channel_response(ch_name, response)

			enemy_data.life_state = ewcfg.enemy_lifestate_alive
			enemy_data.time_lastenter = time_now
			enemy_data.persist()

			target_data = None

		elif check_raidboss_countdown(enemy_data) and enemy_data.life_state == ewcfg.enemy_lifestate_alive:
			# Raid boss attacks.
			pass

		# If a raid boss is currently counting down, delete the previous countdown message to reduce visual clutter.
		elif check_raidboss_countdown(enemy_data) == False:

			target_data = None

			timer = (enemy_data.raidtimer - (int(time.time())) + ewcfg.time_raidcountdown)

			if timer < ewcfg.enemy_attack_tick_length and timer != 0:
				timer = ewcfg.enemy_attack_tick_length

			countdown_response = "A sinister presence is lurking. Time remaining: {} seconds...".format(timer)
			resp_cont.add_channel_response(ch_name, countdown_response)

			#TODO: Edit the countdown message instead of deleting and reposting
			last_messages = await resp_cont.post()
			asyncio.ensure_future(fe_utils.delete_last_message(client, last_messages, ewcfg.enemy_attack_tick_length))
			
			# Don't post resp_cont a second time while the countdown is going on.
			should_post_resp_cont = False

		if enemy_data.attacktype != ewcfg.enemy_attacktype_unarmed:
			used_attacktype = hunt_static.attack_type_map.get(enemy_data.attacktype)
		else:
			return

		if target_data != None:

			target_player = EwPlayer(id_user=target_data.id_user)
			target_slimeoid = EwSlimeoid(id_user=target_data.id_user)

			target_weapon = None
			target_weapon_item = None
			if target_data.weapon >= 0:
				target_weapon_item = EwItem(id_item = target_data.weapon)
				target_weapon = static_weapons.weapon_map.get(target_weapon_item.item_props.get("weapon_type"))
			
			server = client.get_guild(target_data.id_server)
			# server = discord.guild(id=target_data.id_server)
			# print(target_data.id_server)
			# channel = discord.utils.get(server.channels, name=ch_name)

			# print(server)

			# member = discord.utils.get(channel.guild.members, name=target_player.display_name)
			# print(member)

			target_mutations = target_data.get_mutations()

			miss = False
			crit = False
			strikes = 0
			#sap_damage = 0
			#sap_ignored = 0
			hit_chance_mod = 0
			crit_mod = 0
			dmg_mod = 0

			# Weaponized flavor text.
			#randombodypart = ewcfg.hitzone_list[random.randrange(len(ewcfg.hitzone_list))]
			hitzone = ewwep.get_hitzone()
			randombodypart = hitzone.name
			if random.random() < 0.5:
				randombodypart = random.choice(hitzone.aliases)

			shooter_status_mods = ewwep.get_shooter_status_mods(enemy_data, target_data, hitzone)
			shootee_status_mods = ewwep.get_shootee_status_mods(target_data, enemy_data, hitzone)

			hit_chance_mod += round(shooter_status_mods['hit_chance'] + shootee_status_mods['hit_chance'], 2)
			crit_mod += round(shooter_status_mods['crit'] + shootee_status_mods['crit'], 2)
			dmg_mod += round(shooter_status_mods['dmg'] + shootee_status_mods['dmg'], 2)
			
			# maybe enemies COULD have weapon skills? could punishes players who die to the same enemy without mining up beforehand
			# slimes_damage = int((slimes_spent * 4) * (100 + (user_data.weaponskill * 10)) / 100.0)

			# since enemies dont use up slime or hunger, this is only used for damage calculation
			slimes_spent = int(ewutils.slime_bylevel(enemy_data.level) / 40 * ewcfg.enemy_attack_tick_length / 2)

			slimes_damage = int(slimes_spent * 4)

			if used_attacktype == ewcfg.enemy_attacktype_body:
				slimes_damage /= 2  # specific to juvies
			if enemy_data.enemytype == ewcfg.enemy_type_microslime:
				slimes_damage *= 20  # specific to microslime
				
			if enemy_data.weathertype == ewcfg.enemy_weathertype_rainresist:
				slimes_damage *= 1.5

			slimes_damage += int(slimes_damage * dmg_mod)

			#slimes_dropped = target_data.totaldamage + target_data.slimes

			target_iskillers = target_data.life_state == ewcfg.life_state_enlisted and target_data.faction == ewcfg.faction_killers
			target_isrowdys = target_data.life_state == ewcfg.life_state_enlisted and target_data.faction == ewcfg.faction_rowdys
			target_isslimecorp = target_data.life_state == ewcfg.life_state_enlisted and target_data.faction == ewcfg.faction_slimecorp
			target_isexecutive = target_data.life_state in [ewcfg.life_state_lucky, ewcfg.life_state_executive]
			target_isjuvie = target_data.life_state == ewcfg.life_state_juvenile
			target_isnotdead = target_data.life_state != ewcfg.life_state_corpse
			target_isshambler = target_data.life_state == ewcfg.life_state_shambler

			if target_data.life_state == ewcfg.life_state_kingpin:
				# Disallow killing generals.
				response = "The {} tries to attack the kingpin, but is taken aback by the sheer girth of their slime.".format(enemy_data.display_name)
				resp_cont.add_channel_response(ch_name, response)

			elif (time_now - target_data.time_lastrevive) < ewcfg.invuln_onrevive:
				# User is currently invulnerable.
				response = "The {} tries to attack {}, but they have died too recently and are immune.".format(
					enemy_data.display_name,
					target_player.display_name)
				resp_cont.add_channel_response(ch_name, response)

			# enemies dont fuck with ghosts, ghosts dont fuck with enemies.
			elif (target_iskillers or target_isrowdys or target_isjuvie or target_isexecutive or target_isshambler or target_isslimecorp) and (target_isnotdead):
				was_killed = False
				was_hurt = False

				if target_data.life_state in [ewcfg.life_state_shambler, ewcfg.life_state_enlisted, ewcfg.life_state_juvenile, ewcfg.life_state_lucky, ewcfg.life_state_executive]:

					# If a target is being attacked by an enemy with the defender ai, check to make sure it can be hit.
					if (enemy_data.ai == ewcfg.enemy_ai_defender) and (hunt_utils.check_defender_targets(target_data, enemy_data) == False):
						return
					else:
						# Target can be hurt by enemies.
						was_hurt = True

				if was_hurt:
					# Attacking-type-specific adjustments
					if used_attacktype != ewcfg.enemy_attacktype_unarmed and used_attacktype.fn_effect != None:
						# Build effect container
						ctn = EwEnemyEffectContainer(
							miss=miss,
							crit=crit,
							slimes_damage=slimes_damage,
							enemy_data=enemy_data,
							target_data=target_data,
							#sap_damage=sap_damage,
							#sap_ignored=sap_ignored,
							hit_chance_mod=hit_chance_mod,
							crit_mod=crit_mod
						)

						# Make adjustments
						used_attacktype.fn_effect(ctn)

						# Apply effects for non-reference values
						miss = ctn.miss
						crit = ctn.crit
						slimes_damage = ctn.slimes_damage
						strikes = ctn.strikes
						#sap_damage = ctn.sap_damage
						#sap_ignored = ctn.sap_ignored

					# can't hit lucky lucy
					if target_data.life_state == ewcfg.life_state_lucky:
						miss = True

					if miss:
						slimes_damage = 0
						#sap_damage = 0
						crit = False
	
					#if crit:
					#	sap_damage += 1

					enemy_data.persist()
					target_data = EwUser(id_user = target_data.id_user, id_server = target_data.id_server, data_level = 1)

					# apply defensive mods
					slimes_damage *= ewwep.damage_mod_defend(
						shootee_data = target_data,
						shootee_mutations = target_mutations,
						shootee_weapon = target_weapon,
						market_data = market_data
					)

					#if target_weapon != None:
					#	if sap_damage > 0 and ewcfg.weapon_class_defensive in target_weapon.classes:
					#		sap_damage -= 1

			
					# apply hardened sap armor
					#sap_armor = ewwep.get_sap_armor(shootee_data = target_data, sap_ignored = sap_ignored)
					#slimes_damage *= sap_armor
					#slimes_damage = int(max(slimes_damage, 0))
	
					#sap_damage = min(sap_damage, target_data.hardened_sap)

					#injury_severity = ewwep.get_injury_severity(target_data, slimes_damage, crit)

					if slimes_damage >= target_data.slimes - target_data.bleed_storage:
						was_killed = True
						slimes_damage = max(target_data.slimes - target_data.bleed_storage, 0)

					sewer_data = EwDistrict(district=ewcfg.poi_id_thesewers, id_server=enemy_data.id_server)

					# move around slime as a result of the shot
					if target_isjuvie:
						slimes_drained = int(3 * slimes_damage / 4)  # 3/4
					else:
						slimes_drained = 0

					damage = slimes_damage

					slimes_tobleed = int((slimes_damage - slimes_drained) / 2)
					#if ewcfg.mutation_id_bleedingheart in target_mutations:
					#	slimes_tobleed *= 2

					slimes_directdamage = slimes_damage - slimes_tobleed
					slimes_splatter = slimes_damage - slimes_tobleed - slimes_drained

					# Damage victim's wardrobe (heh, WARdrobe... get it??)
					victim_cosmetics = bknd_item.inventory(
						id_user = target_data.id_user,
						id_server = target_data.id_server,
						item_type_filter = ewcfg.it_cosmetic
					)

					onbreak_responses = []

					# the following code handles cosmetic durability loss
					
					# for cosmetic in victim_cosmetics:
					# 	if not int(cosmetic.get('soulbound')) == 1:
					# 		c = EwItem(cosmetic.get('id_item'))
					# 
					# 		# Damage it if the cosmetic is adorned and it has a durability limit
					# 		if c.item_props.get("adorned") == 'true' and c.item_props['durability'] is not None:
					# 
					# 			#print("{} current durability: {}:".format(c.item_props.get("cosmetic_name"), c.item_props['durability']))
					# 
					# 			durability_afterhit = int(c.item_props['durability']) - slimes_damage
					# 
					# 			#print("{} durability after next hit: {}:".format(c.item_props.get("cosmetic_name"), durability_afterhit))
					# 
					# 			if durability_afterhit <= 0:  # If it breaks
					# 				c.item_props['durability'] = durability_afterhit
					# 				c.persist()
					# 
					# 
					# 				target_data.persist()
					# 
					# 				onbreak_responses.append(
					# 					str(c.item_props['str_onbreak']).format(c.item_props['cosmetic_name']))
					# 
					# 				ewitem.item_delete(id_item = c.id_item)
					# 
					# 			else:
					# 				c.item_props['durability'] = durability_afterhit
					# 				c.persist()
					# 
					# 		else:
					# 			pass




					market_data.splattered_slimes += slimes_damage
					market_data.persist()
					district_data.change_slimes(n=slimes_splatter, source=ewcfg.source_killing)
					target_data.bleed_storage += slimes_tobleed
					target_data.change_slimes(n=-slimes_directdamage, source=ewcfg.source_damage)
					target_data.time_lasthit = int(time_now)

					#target_data.hardened_sap -= sap_damage
					sewer_data.change_slimes(n=slimes_drained)

					if was_killed:

						# Dedorn player cosmetics
						#ewitem.item_dedorn_cosmetics(id_server=target_data.id_server, id_user=target_data.id_user)
						# Drop all items into district
						#bknd_item.item_dropall(target_data)

						# Give a bonus to the player's weapon skill for killing a stronger player.
						# if target_data.slimelevel >= user_data.slimelevel and weapon is not None:
						# enemy_data.add_weaponskill(n = 1, weapon_type = weapon.id_weapon)

						explode_damage = ewutils.slime_bylevel(target_data.slimelevel) / 5
						# explode, damaging everyone in the district

						# release bleed storage
						slimes_todistrict = target_data.slimes

						district_data.change_slimes(n=slimes_todistrict, source=ewcfg.source_killing)

						# Player was killed. Remove its id from enemies with defender ai.
						enemy_data.id_target = -1
						target_data.id_killer = enemy_data.id_enemy

						#target_data.change_slimes(n=-slimes_dropped / 10, source=ewcfg.source_ghostification)
						civ_weapon = random.choice(ewcfg.makeshift_weapons)

						kill_descriptor = "beaten to death"
						if used_attacktype != ewcfg.enemy_attacktype_unarmed:
							response = used_attacktype.str_damage.format(
								name_enemy=enemy_data.display_name,
								name_target=("<@!{}>".format(target_data.id_user)),
								hitzone=randombodypart,
								strikes=strikes,
								civ_weapon=civ_weapon
							)
							kill_descriptor = used_attacktype.str_killdescriptor
							if crit:
								response += " {}".format(used_attacktype.str_crit.format(
									name_enemy=enemy_data.display_name,
									name_target=target_player.display_name,
									civ_weapon=civ_weapon
								))

							if len(onbreak_responses) != 0:
								for onbreak_response in onbreak_responses:
									response += "\n\n" + onbreak_response

							response += "\n\n{}".format(used_attacktype.str_kill.format(
								name_enemy=enemy_data.display_name,
								name_target=("<@!{}>".format(target_data.id_user)),
								emote_skull=ewcfg.emote_slimeskull,
								civ_weapon=civ_weapon
							))
							target_data.trauma = used_attacktype.id_type

						else:
							response = ""

							if len(onbreak_responses) != 0:
								for onbreak_response in onbreak_responses:
									response = onbreak_response + "\n\n"

							response = "{name_target} is hit!!\n\n{name_target} has died.".format(
								name_target=target_player.display_name)

							target_data.trauma = ewcfg.trauma_id_environment

						if target_slimeoid.life_state == ewcfg.slimeoid_state_active:
							brain = sl_static.brain_map.get(target_slimeoid.ai)
							response += "\n\n" + brain.str_death.format(slimeoid_name=target_slimeoid.name)

						enemy_data.persist()
						district_data.persist()
						die_resp = target_data.die(cause=ewcfg.cause_killing_enemy) # moved after trauma definition so it can gurantee .die knows killer
						district_data = EwDistrict(district = district_data.name, id_server = district_data.id_server)

						target_data.persist()
						resp_cont.add_response_container(die_resp)
						resp_cont.add_channel_response(ch_name, response)

						# don't recreate enemy data if enemy was killed in explosion
						if check_death(enemy_data) == False:
							enemy_data = EwEnemy(id_enemy=self.id_enemy)

						target_data = EwUser(id_user = target_data.id_user, id_server = target_data.id_server, data_level = 1)
					else:
						# A non-lethal blow!
						# apply injury
						#if injury_severity > 0:
						#	target_data.apply_injury(hitzone.id_injury, injury_severity, enemy_data.id_enemy)

						if used_attacktype != ewcfg.enemy_attacktype_unarmed:
							if miss:
								response = "{}".format(used_attacktype.str_miss.format(
									name_enemy=enemy_data.display_name,
									name_target=target_player.display_name
								))
							else:
								response = used_attacktype.str_damage.format(
									name_enemy=enemy_data.display_name,
									name_target=("<@!{}>".format(target_data.id_user)),
									hitzone=randombodypart,
									strikes=strikes,
									civ_weapon = random.choice(ewcfg.makeshift_weapons)
								)
								if crit:
									response += " {}".format(used_attacktype.str_crit.format(
										name_enemy=enemy_data.display_name,
										name_target=target_player.display_name,
										civ_weapon = random.choice(ewcfg.makeshift_weapons)
									))
								#sap_response = ""
								#if sap_damage > 0:
								#	sap_response = " and {sap_damage} hardened sap".format(sap_damage = sap_damage)

								response += " {target_name} loses {damage:,} slime!".format(
									target_name=target_player.display_name,
									damage=damage
									#sap_response=sap_response
								)
								if len(onbreak_responses) != 0:
									for onbreak_response in onbreak_responses:
										response += "\n\n" + onbreak_response
						else:
							if miss:
								response = "{target_name} dodges the {enemy_name}'s strike.".format(
									target_name=target_player.display_name, enemy_name=enemy_data.display_name)
							else:
								response = "{target_name} is hit!! {target_name} loses {damage:,} slime!".format(
									target_name=target_player.display_name,
									damage=damage
								)
							if len(onbreak_responses) != 0:
								for onbreak_response in onbreak_responses:
									response += "\n" + onbreak_response

						resp_cont.add_channel_response(ch_name, response)
				else:
					response = '{} is unable to attack {}.'.format(enemy_data.display_name, target_player.display_name)
					resp_cont.add_channel_response(ch_name, response)

				# Persist user and enemy data.
				if enemy_data.life_state == ewcfg.enemy_lifestate_alive or enemy_data.life_state == ewcfg.enemy_lifestate_unactivated:
					enemy_data.persist()
				target_data.persist()

				district_data.persist()

				# Assign the corpse role to the newly dead player.
				if was_killed:
					member = server.get_member(target_data.id_user)
					await ewrolemgr.updateRoles(client=client, member=member)
					# announce death in kill feed channel
					# killfeed_channel = ewutils.get_channel(enemy_data.id_server, ewcfg.channel_killfeed)
					# killfeed_resp = resp_cont.channel_responses[ch_name]
					# for r in killfeed_resp:
					#	 resp_cont.add_channel_response(ewcfg.channel_killfeed, r)
					# resp_cont.format_channel_response(ewcfg.channel_killfeed, enemy_data)
					# resp_cont.add_channel_response(ewcfg.channel_killfeed, "`-------------------------`")
				# await ewutils.send_message(client, killfeed_channel, ewutils.formatMessage(enemy_data.display_name, killfeed_resp))

		# Send the response to the player.
		resp_cont.format_channel_response(ch_name, enemy_data)
		if should_post_resp_cont:
			await resp_cont.post()
			
	# Function that enemies used to attack each other in Gankers Vs. Shamblers.
	async def cannibalize(self):
		client = ewutils.get_client()

		last_messages = []
		should_post_resp_cont = True

		enemy_data = self

		time_now = int(time.time())
		resp_cont = EwResponseContainer(id_server=enemy_data.id_server)
		district_data = EwDistrict(district=enemy_data.poi, id_server=enemy_data.id_server)
		market_data = EwMarket(id_server=enemy_data.id_server)
		ch_name = poi_static.id_to_poi.get(enemy_data.poi).channel
		
		used_attacktype = hunt_static.attack_type_map.get(enemy_data.attacktype)

		# Get target's info based on its AI.
		target_enemy, group_attack = get_target_by_ai(enemy_data, cannibalize = True)
		
		if enemy_data.enemyclass == ewcfg.enemy_class_gaiaslimeoid:
			if enemy_data.enemy_props.get('primed') != None:
				if enemy_data.enemy_props.get('primed') != 'true':
					return
			
			# target_enemy is a dict, enemy IDs are mapped to their coords
			if len(target_enemy) == 1 and not group_attack:
				#print('gaia found target')
				used_id = None
				
				for key in target_enemy.keys():
					used_id = key
					
				target_enemy = EwEnemy(id_enemy=used_id, id_server=enemy_data.id_server)
				
				# print('gaia changed target_enemy into enemy from dict')
			elif len(target_enemy) == 0:
				target_enemy = None
		
		elif enemy_data.enemyclass == ewcfg.enemy_class_shambler:
			if target_enemy == None:
				return await sh_move(enemy_data)
			elif enemy_data.enemytype == ewcfg.enemy_type_dinoshambler:
				if target_enemy.enemytype == ewcfg.enemy_type_gaia_suganmanuts and enemy_data.enemy_props.get('jumping') == 'true':
					enemy_data.enemy_props['jumping'] = 'false'
				else:
					return await sh_move(enemy_data)

		if check_raidboss_countdown(enemy_data) and enemy_data.life_state == ewcfg.enemy_lifestate_unactivated:
			# Raid boss has activated!
			response = "*The ground quakes beneath your feet as slime begins to pool into one hulking, solidified mass...*" \
					   "\n{} **{} has arrived! It's level {} and has {} slime!** {}\n".format(
				ewcfg.emote_megaslime,
				enemy_data.display_name,
				enemy_data.level,
				enemy_data.slimes,
				ewcfg.emote_megaslime
			)
			resp_cont.add_channel_response(ch_name, response)

			enemy_data.life_state = ewcfg.enemy_lifestate_alive
			enemy_data.time_lastenter = time_now
			enemy_data.persist()

			target_enemy = None

		elif check_raidboss_countdown(enemy_data) and enemy_data.life_state == ewcfg.enemy_lifestate_alive:
			# Raid boss attacks.
			pass

		# If a raid boss is currently counting down, delete the previous countdown message to reduce visual clutter.
		elif check_raidboss_countdown(enemy_data) == False:

			target_enemy = None

			timer = (enemy_data.raidtimer - (int(time.time())) + ewcfg.time_raidcountdown)

			if timer < ewcfg.enemy_attack_tick_length and timer != 0:
				timer = ewcfg.enemy_attack_tick_length

			countdown_response = "A sinister presence is lurking. Time remaining: {} seconds...".format(timer)
			resp_cont.add_channel_response(ch_name, countdown_response)

			# TODO: Edit the countdown message instead of deleting and reposting
			last_messages = await resp_cont.post()
			asyncio.ensure_future(fe_utils.delete_last_message(client, last_messages, ewcfg.enemy_attack_tick_length))

			# Don't post resp_cont a second time while the countdown is going on.
			should_post_resp_cont = False

		if target_enemy != None and not group_attack:
			
			miss = False

			# Weaponized flavor text.
			# hitzone = ewwep.get_hitzone()
			# randombodypart = hitzone.name
			# if random.random() < 0.5:
			# 	randombodypart = random.choice(hitzone.aliases)
			randombodypart = 'brainz' if enemy_data.enemyclass == ewcfg.enemy_class_gaiaslimeoid else 'stem'
			
			slimes_damage = 0
			set_damage = int(enemy_data.enemy_props.get('setdamage'))
			if set_damage != None:
				slimes_damage = set_damage


			# Enemies don't select for these types of lifestates in their AI, this serves as a backup just in case.
			if target_enemy.life_state != ewcfg.enemy_lifestate_unactivated and target_enemy.life_state != ewcfg.enemy_lifestate_dead:
				was_killed = False
				below_full = False
				below_half = False
				was_hurt = True
				
				# Attacking-type-specific adjustments
				if used_attacktype.fn_effect != None:

					# Apply effects for non-reference values
					miss = False # Make sure to account for phosphorpoppies statuses
					
				if miss:
					slimes_damage = 0

				enemy_data.persist()
				target_enemy = EwEnemy(id_enemy = target_enemy.id_enemy, id_server = target_enemy.id_server)

				if slimes_damage >= target_enemy.slimes: # - target_enemy.bleed_storage:
					was_killed = True
					slimes_damage = max(target_enemy.slimes, 0) # - target_enemy.bleed_storage
				else:
					# In Gankers Vs. Shamblers, responses are only sent out after the initial hit and when the target reaches below 50% HP
					# This serves to ensure less responses cluttering up the channel and to preserve performance.
					if target_enemy.slimes < target_enemy.initialslimes and not target_enemy.enemy_props.get('below_full') == 'true':
						target_enemy.enemy_props['below_full'] = 'true'
						below_full = True
					elif target_enemy.slimes < int(target_enemy.initialslimes / 2) and not target_enemy.enemy_props.get('below_half') == 'true':
						target_enemy.enemy_props['below_half'] = 'true'
						below_half = True

				sewer_data = EwDistrict(district=ewcfg.poi_id_thesewers, id_server=enemy_data.id_server)

				# slimes_drained = int(3 * slimes_damage / 4)  # 3/4
				slimes_drained = int(7 * slimes_damage / 8) # 7/8

				damage = slimes_damage

				#slimes_tobleed = int((slimes_damage - slimes_drained) / 2)

				slimes_directdamage = slimes_damage # - slimes_tobleed
				slimes_splatter = slimes_damage - slimes_drained # - slimes_tobleed 

				market_data.splattered_slimes += slimes_damage
				market_data.persist()
				district_data.change_slimes(n=slimes_splatter, source=ewcfg.source_killing)
				#target_enemy.bleed_storage += slimes_tobleed
				target_enemy.change_slimes(n=- slimes_directdamage, source=ewcfg.source_damage)
				sewer_data.change_slimes(n=slimes_drained)
				
				if target_enemy.enemytype == ewcfg.enemy_type_gaia_razornuts:
					bite_response = "{} [{}] ({}) bit on a razornut and got hurt! They lost 20000 slime!".format(enemy_data.display_name, enemy_data.identifier, enemy_data.gvs_coord)
					enemy_data.change_slimes(n=-20000)
					if enemy_data.slimes <= 0:
						bite_response += " The attack killed {} [{}] ({}) in the process.".format(enemy_data.display_name, enemy_data.identifier, enemy_data.gvs_coord)

						delete_enemy(enemy_data)
						resp_cont.add_channel_response(ch_name, bite_response)

						return await resp_cont.post()
					else:
						resp_cont.add_channel_response(ch_name, bite_response)
				elif enemy_data.enemytype == ewcfg.enemy_type_shambleballplayer:
					current_target_coord = target_enemy.gvs_coord
					row = current_target_coord[0]
					column = int(current_target_coord[1])
					
					if column < 9:
						new_coord = "{}{}".format(row, column+1)
						
						gaias_in_coord = hunt_utils.gvs_get_gaias_from_coord(enemy_data.poi, new_coord)
	
						if len(gaias_in_coord) > 0:
							pass
						else:
							punt_response = "{} [{}] ({}) punts a {} into {}!".format(enemy_data.display_name, enemy_data.identifier, enemy_data.gvs_coord, target_enemy.display_name, new_coord)
							resp_cont.add_channel_response(ch_name, punt_response)
							
							target_enemy.gvs_coord = new_coord
							target_enemy.persist()

				if was_killed:
					# Enemy was killed.
					delete_enemy(target_enemy)
					
					# release bleed storage
					slimes_todistrict = target_enemy.slimes

					district_data.change_slimes(n=slimes_todistrict, source=ewcfg.source_killing)
					
					response = used_attacktype.str_damage.format(
						name_enemy=enemy_data.display_name,
						name_target=target_enemy.display_name,
						hitzone=randombodypart,
					)

					response += "\n\n{}".format(used_attacktype.str_kill.format(
						name_enemy=enemy_data.display_name,
						name_target=target_enemy.display_name,
						emote_skull=ewcfg.emote_slimeskull
					))
						
					
					enemy_data.persist()
					district_data.persist()

					resp_cont.add_channel_response(ch_name, response)

					# don't recreate enemy data if enemy was killed in explosion
					if check_death(enemy_data) == False:
						enemy_data = EwEnemy(id_enemy=self.id_enemy)

				else:
					# A non-lethal blow!
					if miss:
						response = "{}".format(used_attacktype.str_miss.format(
							name_enemy=enemy_data.display_name,
							name_target=target_enemy.display_name
						))
					else:
						response = used_attacktype.str_damage.format(
							name_enemy=enemy_data.display_name,
							name_target=target_enemy.display_name,
							hitzone=randombodypart,
						)
						response += " {target_name} loses {damage:,} slime!".format(
							target_name=target_enemy.display_name,
							damage=damage,
						)
							
					# if below_full == False and below_half == False:
					# 	should_post_resp_cont = False
					# 	response = ""
							
					target_enemy.persist()
					resp_cont.add_channel_response(ch_name, response)

				# Persist enemy data.
				if enemy_data.life_state == ewcfg.enemy_lifestate_alive or enemy_data.life_state == ewcfg.enemy_lifestate_unactivated:
					enemy_data.persist()

				district_data.persist()
				
			if enemy_data.attacktype == ewcfg.enemy_attacktype_gvs_g_explosion:
				delete_enemy(enemy_data)
				
		elif target_enemy != None and group_attack:
			# print('group attack...')
			
			for key in target_enemy.keys():
				
				used_id = key
				target_enemy = EwEnemy(id_enemy=used_id, id_server=enemy_data.id_server)

				miss = False
	
				# Weaponized flavor text.
				randombodypart = 'brainz' if enemy_data.enemyclass == ewcfg.enemy_class_gaiaslimeoid else 'stem'
	
				slimes_damage = 0
				set_damage = int(enemy_data.enemy_props.get('setdamage'))
				if set_damage != None:
					slimes_damage = set_damage
	
	
				# Enemies don't select for these types of lifestates in their AI, this serves as a backup just in case.
				if target_enemy.life_state != ewcfg.enemy_lifestate_unactivated and target_enemy.life_state != ewcfg.enemy_lifestate_dead:
					was_killed = False
					below_full = False
					below_half = False
					was_hurt = True
	
					enemy_data.persist()
					target_enemy = EwEnemy(id_enemy=target_enemy.id_enemy, id_server=target_enemy.id_server)
	
					if slimes_damage >= target_enemy.slimes:
						was_killed = True
						slimes_damage = max(target_enemy.slimes, 0) 
					else:
						# In Gankers Vs. Shamblers, responses are only sent out after the initial hit and when the target reaches below 50% HP
						# This serves to ensure less responses cluttering up the channel and to preserve performance.
						if target_enemy.slimes < target_enemy.initialslimes and not target_enemy.enemy_props.get('below_full') == 'true':
							target_enemy.enemy_props['below_full'] = 'true'
							below_full = True
						elif target_enemy.slimes < int(target_enemy.initialslimes / 2) and not target_enemy.enemy_props.get('below_half') == 'true':
							target_enemy.enemy_props['below_half'] = 'true'
							below_half = True
	
					sewer_data = EwDistrict(district=ewcfg.poi_id_thesewers, id_server=enemy_data.id_server)
	
					# slimes_drained = int(3 * slimes_damage / 4)  # 3/4
					slimes_drained = int(7 * slimes_damage / 8)  # 7/8
	
					damage = slimes_damage
	
					# slimes_tobleed = int((slimes_damage - slimes_drained) / 2)
	
					slimes_directdamage = slimes_damage  # - slimes_tobleed
					slimes_splatter = slimes_damage - slimes_drained  # - slimes_tobleed 
	
					market_data.splattered_slimes += slimes_damage
					market_data.persist()
					district_data.change_slimes(n=slimes_splatter, source=ewcfg.source_killing)
					# target_enemy.bleed_storage += slimes_tobleed
					target_enemy.change_slimes(n=- slimes_directdamage, source=ewcfg.source_damage)
					sewer_data.change_slimes(n=slimes_drained)
	
					if was_killed:
						# Enemy was killed.
						delete_enemy(target_enemy)
	
						# release bleed storage
						slimes_todistrict = target_enemy.slimes
	
						district_data.change_slimes(n=slimes_todistrict, source=ewcfg.source_killing)
	
						# target_data.change_slimes(n=-slimes_dropped / 10, source=ewcfg.source_ghostification)
						
						response = used_attacktype.str_damage.format(
							name_enemy=enemy_data.display_name,
							name_target=target_enemy.display_name,
							hitzone=randombodypart,
						)
	
						response += "\n\n{}".format(used_attacktype.str_kill.format(
							name_enemy=enemy_data.display_name,
							name_target=target_enemy.display_name,
							emote_skull=ewcfg.emote_slimeskull
						))
	
						enemy_data.persist()
						district_data.persist()
	
						resp_cont.add_channel_response(ch_name, response)
	
						# don't recreate enemy data if enemy was killed in explosion
						if check_death(enemy_data) == False:
							enemy_data = EwEnemy(id_enemy=self.id_enemy)
	
					else:
						# A non-lethal blow!
						
						if miss:
							response = "{}".format(used_attacktype.str_miss.format(
								name_enemy=enemy_data.display_name,
								name_target=target_enemy.display_name
							))
						else:
							response = used_attacktype.str_damage.format(
								name_enemy=enemy_data.display_name,
								name_target=target_enemy.display_name,
								hitzone=randombodypart,
							)
							response += " {target_name} loses {damage:,} slime!".format(
								target_name=target_enemy.display_name,
								damage=damage,
							)
	
						# if below_full == False and below_half == False:
						# 	should_post_resp_cont = False
						# 	response = ""
	
						target_enemy.persist()
						resp_cont.add_channel_response(ch_name, response)
	
					# Persist enemy data.
					if enemy_data.life_state == ewcfg.enemy_lifestate_alive or enemy_data.life_state == ewcfg.enemy_lifestate_unactivated:
						enemy_data.persist()

				district_data.persist()

			if enemy_data.attacktype == ewcfg.enemy_attacktype_gvs_g_explosion:
				delete_enemy(enemy_data)

		# Send the response to the player.
		resp_cont.format_channel_response(ch_name, enemy_data)
		if should_post_resp_cont:
			await resp_cont.post()

	def move(self):
		resp_cont = EwResponseContainer(id_server=self.id_server)

		old_district_response = ""
		new_district_response = ""
		gang_base_response = ""

		try:
			# Raid bosses can move into other parts of the outskirts as well as the city, including district zones.
			destinations = set(poi_static.poi_neighbors.get(self.poi))
			
			if self.enemytype in ewcfg.gvs_enemies:
				path = [ewcfg.poi_id_assaultflatsbeach, ewcfg.poi_id_vagrantscorner, ewcfg.poi_id_greenlightdistrict, ewcfg.poi_id_downtown]
				
				if self.poi == path[0]:
					destinations = [path[1]]
				elif self.poi == path[1]:
					destinations = [path[2]]
				elif self.poi == path[2]:
					destinations = [path[3]]
				elif self.poi == path[3]:
					# Raid boss has finished its path
					return
			
			# Filter subzones and gang bases out.
			# Nudge raidbosses into the city.
			for destination in destinations:

				destination_poi_data = poi_static.id_to_poi.get(destination)
				if destination_poi_data.is_subzone or destination_poi_data.is_gangbase:
					destinations.remove(destination)
				
				if self.poi in poi_static.outskirts_depths:
					if destination in poi_static.outskirts_depths:
						destinations.remove(destination)
				elif self.poi in poi_static.outskirts_middle:
					if (destination in poi_static.outskirts_middle) or (destination in poi_static.outskirts_depths):
						destinations.remove(destination)
				elif self.poi in poi_static.outskirts_edges: 
					if (destination in poi_static.outskirts_edges) or (destination in poi_static.outskirts_middle):
						destinations.remove(destination)
					

			if len(destinations) > 0:
				
				old_poi = self.poi
				new_poi = random.choice(list(destinations))
					
				self.poi = new_poi
				self.time_lastenter = int(time.time())
				self.id_target = -1

				# print("DEBUG - {} MOVED FROM {} TO {}".format(self.display_name, old_poi, new_poi))

				#new_district = EwDistrict(district=new_poi, id_server=self.id_server)
				#if len(new_district.get_enemies_in_district() > 0:

				# When a raid boss enters a new district, give it a blank identifier
				self.identifier = ''

				new_poi_def = poi_static.id_to_poi.get(new_poi)
				new_ch_name = new_poi_def.channel
				new_district_response = "*A low roar booms throughout the district, as slime on the ground begins to slosh all around.*\n {} **{} has arrived!** {}".format(
					ewcfg.emote_megaslime,
					self.display_name,
					ewcfg.emote_megaslime
				)
				resp_cont.add_channel_response(new_ch_name, new_district_response)

				old_district_response = "{} has moved to {}!".format(self.display_name, new_poi_def.str_name)
				old_poi_def = poi_static.id_to_poi.get(old_poi)
				old_ch_name = old_poi_def.channel
				resp_cont.add_channel_response(old_ch_name, old_district_response)
				
				if new_poi not in poi_static.outskirts:
					gang_base_response = "There are reports of a powerful enemy roaming around {}.".format(new_poi_def.str_name)
					channels = ewcfg.hideout_channels
					for ch in channels:
						resp_cont.add_channel_response(ch, gang_base_response)
		finally:
			self.persist()
			return resp_cont

	def change_slimes(self, n=0, source=None):
		change = int(n)
		self.slimes += change

		if n < 0:
			change *= -1  # convert to positive number
			if source == ewcfg.source_damage or source == ewcfg.source_bleeding or source == ewcfg.source_self_damage:
				self.totaldamage += change

		self.persist()
	
	def getStatusEffects(self):
		values = []

		try:
			data = bknd_core.execute_sql_query("SELECT {id_status} FROM enemy_status_effects WHERE {id_server} = %s and {id_enemy} = %s".format(
				id_status = ewcfg.col_id_status,
				id_server = ewcfg.col_id_server,
				id_enemy = ewcfg.col_id_enemy
			), (
				self.id_server,
				self.id_enemy
			))

			for row in data:
				values.append(row[0])

		except:
			pass
		finally:
			return values

	def applyStatus(self, id_status = None, value = 0, source = "", multiplier = 1, id_target = -1):
		response = ""
		if id_status != None:
			status = None

			status = se_static.status_effects_def_map.get(id_status)
			time_expire = status.time_expire * multiplier

			if status != None:
				statuses = self.getStatusEffects()

				status_effect = EwEnemyStatusEffect(id_status=id_status, enemy_data=self, time_expire=time_expire, value=value, source=source, id_target=id_target)
				
				if id_status in statuses:
					status_effect.value = value

					if status.time_expire > 0 and id_status in ewcfg.stackable_status_effects:
						status_effect.time_expire += time_expire
						response = status.str_acquire

					status_effect.persist()
				else:
					response = status.str_acquire
					
		return response		

	def clear_status(self, id_status = None):
		if id_status != None:
			try:
				conn_info = bknd_core.databaseConnect()
				conn = conn_info.get('conn')
				cursor = conn.cursor()

				# Save the object.
				cursor.execute("DELETE FROM enemy_status_effects WHERE {id_status} = %s and {id_enemy} = %s and {id_server} = %s".format(
					id_status = ewcfg.col_id_status,
					id_enemy = ewcfg.col_id_enemy,
					id_server = ewcfg.col_id_server
				), (
					id_status,
					self.id_enemy,
					self.id_server
				))

				conn.commit()
			finally:
				# Clean up the database handles.
				cursor.close()
				bknd_core.databaseClose(conn_info)

	def clear_allstatuses(self):
		try:
			bknd_core.execute_sql_query("DELETE FROM enemy_status_effects WHERE {id_server} = %s AND {id_enemy} = %s".format(
					id_server = ewcfg.col_id_server,
					id_enemy = ewcfg.col_id_enemy
				),(
					self.id_server,
					self.id_enemy
				))
		except:
			ewutils.logMsg("Failed to clear status effects for enemy {}.".format(self.id_enemy))
	
	def dodge(self):
		enemy_data = self 

		resp_cont = EwResponseContainer(id_server=enemy_data.id_server)
		
		target_data = None

		# Get target's info based on its AI.

		if enemy_data.ai == ewcfg.enemy_ai_coward:
			users = bknd_core.execute_sql_query(
				"SELECT {id_user}, {life_state} FROM users WHERE {poi} = %s AND {id_server} = %s AND NOT ({life_state} = {life_state_corpse} OR {life_state} = {life_state_kingpin})".format(
					id_user=ewcfg.col_id_user,
					life_state=ewcfg.col_life_state,
					poi=ewcfg.col_poi,
					id_server=ewcfg.col_id_server,
					life_state_corpse=ewcfg.life_state_corpse,
					life_state_kingpin=ewcfg.life_state_kingpin,
				), (
					enemy_data.poi,
					enemy_data.id_server
				))
			if len(users) > 0:
				target_data = EwUser(id_user = random.choice(users)[0], id_server = enemy_data.id_server)
		elif enemy_data.ai == ewcfg.enemy_ai_defender:
			if enemy_data.id_target != -1:
				target_data = EwUser(id_user=enemy_data.id_target, id_server=enemy_data.id_server)
		else:
			target_data, group_attack = get_target_by_ai(enemy_data)

		if target_data != None:
			target = EwPlayer(id_user = target_data.id_user, id_server = enemy_data.id_server)
			ch_name = poi_static.id_to_poi.get(enemy_data.poi).channel 

			id_status = ewcfg.status_evasive_id

			enemy_data.clear_status(id_status = id_status)

			enemy_data.applyStatus(id_status = id_status, source = enemy_data.id_enemy, id_target = (target_data.id_user if target_data.combatant_type == "player" else target_data.id_enemy))

			response = "{} focuses on dodging {}'s attacks.".format(enemy_data.display_name, target.display_name)
			resp_cont.add_channel_response(ch_name, response)
		
		return resp_cont

	def taunt(self):
		enemy_data = self 

		resp_cont = EwResponseContainer(id_server=enemy_data.id_server)
		
		target_data = None

		# Get target's info based on its AI.

		if enemy_data.ai == ewcfg.enemy_ai_coward:
			return
		elif enemy_data.ai == ewcfg.enemy_ai_defender:
			if enemy_data.id_target != -1:
				target_data = EwUser(id_user=enemy_data.id_target, id_server=enemy_data.id_server)
		else:
			target_data, group_attack = get_target_by_ai(enemy_data)

		if target_data != None:
			target = EwPlayer(id_user = target_data.id_user, id_server = enemy_data.id_server)
			ch_name = poi_static.id_to_poi.get(enemy_data.poi).channel 

			id_status = ewcfg.status_taunted_id

			target_statuses = target_data.getStatusEffects()

			if id_status in target_statuses:
				return
				
			target_data.applyStatus(id_status = id_status, source = enemy_data.id_enemy, id_target = enemy_data.id_enemy)

			response = "{} taunts {} into attacking it.".format(enemy_data.display_name, target.display_name)
			resp_cont.add_channel_response(ch_name, response)
		
		return resp_cont

	def aim(self):
		enemy_data = self 

		resp_cont = EwResponseContainer(id_server=enemy_data.id_server)
		
		target_data = None

		# Get target's info based on its AI.

		if enemy_data.ai == ewcfg.enemy_ai_coward:
			return
		elif enemy_data.ai == ewcfg.enemy_ai_defender:
			if enemy_data.id_target != -1:
				target_data = EwUser(id_user=enemy_data.id_target, id_server=enemy_data.id_server)
		else:
			target_data, group_attack = get_target_by_ai(enemy_data)

		if target_data != None:
			target = EwPlayer(id_user = target_data.id_user, id_server = enemy_data.id_server)
			ch_name = poi_static.id_to_poi.get(enemy_data.poi).channel 

			id_status = ewcfg.status_aiming_id

			enemy_data.clear_status(id_status = id_status)

			enemy_data.applyStatus(id_status = id_status, source = enemy_data.id_enemy, id_target = (target_data.id_user if target_data.combatant_type == "player" else target_data.id_enemy))

			enemy_data.persist()

			response = "{} aims at {}'s weak spot.".format(enemy_data.display_name, target.display_name)
			resp_cont.add_channel_response(ch_name, response)
		
		return resp_cont
	
	@property
	def slimelevel(self):
		return self.level

		
class EwOperationData:
	
	# The ID of the user who chose a seedpacket/tombstone for that operation
	id_user = 0
	
	# The district that the operation takes place in
	district = ""
	
	# The enemytype associated with that seedpacket/tombstone.
	# A single Garden Ganker can not choose two of the same enemytype. No duplicate tombstones are allowed at all.
	enemytype = ""
	
	# The 'faction' of whoever chose that enemytype. This is either set to 'gankers' or 'shamblers'.
	faction = ""
	
	# The ID of the item used in the operation
	id_item = 0
	
	# The amount of shamblers stored in a tombstone.
	shambler_stock = 0

	def __init__(
		self,
		id_user = -1,
		district = "",
		enemytype = "",
		faction = "",
		id_item = -1,
		shambler_stock = 0,
	):
		self.id_user = id_user
		self.district = district
		self.enemytype = enemytype
		self.faction = faction
		self.id_item = id_item
		self.shambler_stock = shambler_stock
		
		if(id_user != ""):

			try:
				conn_info = bknd_core.databaseConnect()
				conn = conn_info.get('conn')
				cursor = conn.cursor()
	
				# Retrieve object
				cursor.execute("SELECT {}, {}, {} FROM gvs_ops_choices WHERE {} = %s AND {} = %s AND {} = %s".format(
					ewcfg.col_faction,
					ewcfg.col_id_item,
					ewcfg.col_shambler_stock,
					
					ewcfg.col_id_user,
					ewcfg.col_district,
					ewcfg.col_enemy_type
				), (
					self.id_user,
					self.district,
					self.enemytype,
				))
				result = cursor.fetchone()
	
				if result != None:
					# Record found: apply the data to this object.
					self.faction = result[0]
					self.id_item = result[1]
					self.shambler_stock = result[2]
				else:
					# Create a new database entry if the object is missing.
					cursor.execute("REPLACE INTO gvs_ops_choices({}, {}, {}, {}, {}, {}) VALUES(%s, %s, %s, %s, %s, %s)".format(
						ewcfg.col_id_user,
						ewcfg.col_district,
						ewcfg.col_enemy_type,
						ewcfg.col_faction,
						ewcfg.col_id_item,
						ewcfg.col_shambler_stock,
					), (
						self.id_user,
						self.district,
						self.enemytype,
						self.faction,
						self.id_item,
						self.shambler_stock,
					))
	
					conn.commit()

			finally:
				# Clean up the database handles.
				cursor.close()
				bknd_core.databaseClose(conn_info)

	def persist(self):
		try:
			conn_info = bknd_core.databaseConnect()
			conn = conn_info.get('conn')
			cursor = conn.cursor()

			# Save the object.
			cursor.execute("REPLACE INTO gvs_ops_choices({}, {}, {}, {}, {}, {}) VALUES(%s, %s, %s, %s, %s, %s)".format(
				ewcfg.col_id_user,
				ewcfg.col_district,
				ewcfg.col_enemy_type,
				ewcfg.col_faction,
				ewcfg.col_id_item,
				ewcfg.col_shambler_stock
			), (
				self.id_user,
				self.district,
				self.enemytype,
				self.faction,
				self.id_item,
				self.shambler_stock
			))

			conn.commit()
		finally:
			# Clean up the database handles.
			cursor.close()
			bknd_core.databaseClose(conn_info)
	
	def delete(self):
		try:
			conn_info = bknd_core.databaseConnect()
			conn = conn_info.get('conn')
			cursor = conn.cursor()

			cursor.execute("DELETE FROM gvs_ops_choices WHERE {id_user} = %s AND {enemytype} = %s AND {district} = %s".format(
				id_user=ewcfg.col_id_user,
				enemytype=ewcfg.col_enemy_type,
				district=ewcfg.col_district,
			), (
				self.id_user,
				self.enemytype,
				self.district
			))
			
		finally:
			# Clean up the database handles.
			cursor.close()
			bknd_core.databaseClose(conn_info)


# Selects which non-ghost user to attack based on certain parameters.
def get_target_by_ai(enemy_data, cannibalize=False):
	target_data = None
	group_attack = False

	time_now = int(time.time())

	# If a player's time_lastenter is less than this value, it can be attacked.
	targettimer = time_now - ewcfg.time_enemyaggro
	raidbossaggrotimer = time_now - ewcfg.time_raidbossaggro

	if not cannibalize:
		if enemy_data.ai == ewcfg.enemy_ai_defender:
			if enemy_data.id_target != -1:
				target_data = EwUser(id_user=enemy_data.id_target, id_server=enemy_data.id_server, data_level=1)

		elif enemy_data.ai == ewcfg.enemy_ai_attacker_a:
			users = bknd_core.execute_sql_query(
				# "SELECT {id_user}, {life_state}, {time_lastenter} FROM users WHERE {poi} = %s AND {id_server} = %s AND {time_lastenter} < {targettimer} AND ({level} > {safe_level} OR {life_state} != {life_state_juvenile}) AND NOT ({life_state} = {life_state_corpse} OR {life_state} = {life_state_kingpin} OR {id_user} IN (SELECT {id_user} FROM status_effects WHERE id_status = '{repel_status}')) ORDER BY {time_lastenter} ASC".format(
				"SELECT {id_user}, {life_state}, {time_lastenter} FROM users WHERE {poi} = %s AND {id_server} = %s AND {time_lastenter} < {targettimer} AND ({life_state} != {life_state_juvenile}) AND NOT ({life_state} = {life_state_corpse} OR {life_state} = {life_state_kingpin} OR {id_user} IN (SELECT {id_user} FROM status_effects WHERE id_status = '{repel_status}')) ORDER BY {time_lastenter} ASC".format(
					id_user=ewcfg.col_id_user,
					life_state=ewcfg.col_life_state,
					time_lastenter=ewcfg.col_time_lastenter,
					poi=ewcfg.col_poi,
					id_server=ewcfg.col_id_server,
					targettimer=targettimer,
					life_state_corpse=ewcfg.life_state_corpse,
					life_state_kingpin=ewcfg.life_state_kingpin,
					life_state_juvenile=ewcfg.life_state_juvenile,
					repel_status=ewcfg.status_repelled_id,
					slimes=ewcfg.col_slimes,
					# safe_level = ewcfg.max_safe_level,
					level=ewcfg.col_slimelevel
				), (
					enemy_data.poi,
					enemy_data.id_server
				))
			if len(users) > 0:
				target_data = EwUser(id_user=users[0][0], id_server=enemy_data.id_server, data_level=1)

		elif enemy_data.ai == ewcfg.enemy_ai_attacker_b:
			users = bknd_core.execute_sql_query(
				# "SELECT {id_user}, {life_state}, {slimes} FROM users WHERE {poi} = %s AND {id_server} = %s AND {time_lastenter} < {targettimer} AND ({level} > {safe_level} OR {life_state} != {life_state_juvenile}) AND NOT ({life_state} = {life_state_corpse} OR {life_state} = {life_state_kingpin} OR {id_user} IN (SELECT {id_user} FROM status_effects WHERE id_status = '{repel_status}')) ORDER BY {slimes} DESC".format(
				"SELECT {id_user}, {life_state}, {slimes} FROM users WHERE {poi} = %s AND {id_server} = %s AND {time_lastenter} < {targettimer} AND ({life_state} != {life_state_juvenile}) AND NOT ({life_state} = {life_state_corpse} OR {life_state} = {life_state_kingpin} OR {id_user} IN (SELECT {id_user} FROM status_effects WHERE id_status = '{repel_status}')) ORDER BY {slimes} DESC".format(
					id_user=ewcfg.col_id_user,
					life_state=ewcfg.col_life_state,
					slimes=ewcfg.col_slimes,
					poi=ewcfg.col_poi,
					id_server=ewcfg.col_id_server,
					time_lastenter=ewcfg.col_time_lastenter,
					targettimer=targettimer,
					life_state_corpse=ewcfg.life_state_corpse,
					life_state_kingpin=ewcfg.life_state_kingpin,
					life_state_juvenile=ewcfg.life_state_juvenile,
					repel_status=ewcfg.status_repelled_id,
					# safe_level = ewcfg.max_safe_level,
					level=ewcfg.col_slimelevel
				), (
					enemy_data.poi,
					enemy_data.id_server
				))
			if len(users) > 0:
				target_data = EwUser(id_user=users[0][0], id_server=enemy_data.id_server, data_level=1)

		elif enemy_data.ai == ewcfg.enemy_ai_gaiaslimeoid:

			users = bknd_core.execute_sql_query(
				"SELECT {id_user}, {life_state}, {slimes} FROM users WHERE {poi} = %s AND {id_server} = %s AND {time_lastenter} < {targettimer} AND ({life_state} = {life_state_shambler}) ORDER BY {slimes} DESC".format(
					id_user=ewcfg.col_id_user,
					life_state=ewcfg.col_life_state,
					slimes=ewcfg.col_slimes,
					poi=ewcfg.col_poi,
					id_server=ewcfg.col_id_server,
					time_lastenter=ewcfg.col_time_lastenter,
					targettimer=targettimer,
					life_state_shambler=ewcfg.life_state_shambler,
					time_now=time_now,
				), (
					enemy_data.poi,
					enemy_data.id_server
				))
			if len(users) > 0:
				target_data = EwUser(id_user=users[0][0], id_server=enemy_data.id_server, data_level=1)

		elif enemy_data.ai == ewcfg.enemy_ai_shambler:

			users = bknd_core.execute_sql_query(
				"SELECT {id_user}, {life_state}, {slimes} FROM users WHERE {poi} = %s AND {id_server} = %s AND {time_lastenter} < {targettimer} AND NOT ({life_state} = {life_state_shambler} OR {life_state} = {life_state_corpse} OR {life_state} = {life_state_kingpin}) ORDER BY {slimes} DESC".format(
					id_user=ewcfg.col_id_user,
					life_state=ewcfg.col_life_state,
					slimes=ewcfg.col_slimes,
					poi=ewcfg.col_poi,
					id_server=ewcfg.col_id_server,
					time_lastenter=ewcfg.col_time_lastenter,
					targettimer=targettimer,
					life_state_shambler=ewcfg.life_state_shambler,
					life_state_corpse=ewcfg.life_state_corpse,
					life_state_kingpin=ewcfg.life_state_kingpin,
				), (
					enemy_data.poi,
					enemy_data.id_server
				))
			if len(users) > 0:
				target_data = EwUser(id_user=users[0][0], id_server=enemy_data.id_server, data_level=1)

		# If an enemy is a raidboss, don't let it attack until some time has passed when entering a new district.
		if enemy_data.enemytype in ewcfg.raid_bosses and enemy_data.time_lastenter > raidbossaggrotimer:
			target_data = None

	elif cannibalize:
		if enemy_data.ai == ewcfg.enemy_ai_gaiaslimeoid:

			range = 1 if enemy_data.enemy_props.get('range') == None else int(enemy_data.enemy_props.get('range'))
			direction = 'right' if enemy_data.enemy_props.get('direction') == None else enemy_data.enemy_props.get(
				'direction')
			piercing = 'false' if enemy_data.enemy_props.get('piercing') == None else enemy_data.enemy_props.get(
				'piercing')
			splash = 'false' if enemy_data.enemy_props.get('splash') == None else enemy_data.enemy_props.get('splash')
			pierceamount = '0' if enemy_data.enemy_props.get('pierceamount') == None else enemy_data.enemy_props.get(
				'pierceamount')
			singletilepierce = 'false' if enemy_data.enemy_props.get(
				'singletilepierce') == None else enemy_data.enemy_props.get('singletilepierce')

			enemies = ga_check_coord_for_shambler(enemy_data, range, direction, piercing, splash, pierceamount,
												  singletilepierce)
			if len(enemies) > 1:
				group_attack = True

			target_data = enemies

		elif enemy_data.ai == ewcfg.enemy_ai_shambler:
			range = 1 if enemy_data.enemy_props.get('range') == None else int(enemy_data.enemy_props.get('range'))
			direction = 'left' if enemy_data.enemy_props.get('direction') == None else enemy_data.enemy_props.get(
				'direction')

			enemies = sh_check_coord_for_gaia(enemy_data, range, direction)
			if len(enemies) > 0:
				target_data = EwEnemy(id_enemy=enemies[0], id_server=enemy_data.id_server)

		# If an enemy is a raidboss, don't let it attack until some time has passed when entering a new district.
		if enemy_data.enemytype in ewcfg.raid_bosses and enemy_data.time_lastenter > raidbossaggrotimer:
			target_data = None

	return target_data, group_attack

# Check if raidboss is ready to attack / be attacked
def check_raidboss_countdown(enemy_data):
	time_now = int(time.time())

	# Wait for raid bosses
	if enemy_data.enemytype in ewcfg.raid_bosses and enemy_data.raidtimer <= time_now - ewcfg.time_raidcountdown:
		# Raid boss has activated!
		return True
	elif enemy_data.enemytype in ewcfg.raid_bosses and enemy_data.raidtimer > time_now - ewcfg.time_raidcountdown:
		# Raid boss hasn't activated.
		return False

# Check if an enemy is dead. Implemented to prevent enemy data from being recreated when not necessary.
def check_death(enemy_data):
	if enemy_data.slimes <= 0 or enemy_data.life_state == ewcfg.enemy_lifestate_dead:
		# delete_enemy(enemy_data)
		return True
	else:
		return False


async def sh_move(enemy_data):
	current_coord = enemy_data.gvs_coord
	has_moved = False
	index = None
	row = None
	new_coord = None

	if current_coord in ewcfg.gvs_coords_start and enemy_data.enemytype == ewcfg.enemy_type_juvieshambler:
		delete_enemy(enemy_data)

	if current_coord not in ewcfg.gvs_coords_end:
		for row in ewcfg.gvs_valid_coords_shambler:

			if current_coord in row:
				index = row.index(current_coord)
				new_coord = row[index - 1]
				# print(new_coord)
				break

		if new_coord == None:
			return

		enemy_data.gvs_coord = new_coord
		enemy_data.persist()

		for gaia_row in ewcfg.gvs_valid_coords_gaia:
			if new_coord in gaia_row and index != None and row != None:
				poi_channel = poi_static.id_to_poi.get(enemy_data.poi).channel

				try:
					previous_gaia_coord = row[index - 2]
				except:
					break

				response = "The {} moved from {} to {}!".format(enemy_data.display_name, new_coord, previous_gaia_coord)
				client = ewutils.get_client()
				server = client.get_guild(enemy_data.id_server)
				channel = fe_utils.get_channel(server, poi_channel)

				await fe_utils.send_message(client, channel, response)

	# print('shambler moved from {} to {} in {}.'.format(current_coord, new_coord, enemy_data.poi))

	return has_moved


# Deletes an enemy the database.
def delete_enemy(enemy_data):
	# print("DEBUG - {} - {} DELETED".format(enemy_data.id_enemy, enemy_data.display_name))
	enemy_data.clear_allstatuses()
	bknd_core.execute_sql_query("DELETE FROM enemies WHERE {id_enemy} = %s".format(
		id_enemy=ewcfg.col_id_enemy
	), (
		enemy_data.id_enemy,
	))


def ga_check_coord_for_shambler(enemy_data, ga_range, direction, piercing, splash, pierceamount, singletilepierce):
	current_coord = enemy_data.gvs_coord
	detected_shamblers = {}

	for sh_row in ewcfg.gvs_valid_coords_shambler:

		if current_coord in sh_row:
			index = sh_row.index(current_coord)
			checked_coords = gvs_grid_gather_coords(enemy_data.enemyclass, int(ga_range), direction, sh_row, index)

			# print('GAIA -- CHECKED COORDS FOR {} WITH ID {}: {}'.format(enemy_data.enemytype, enemy_data.id_enemy, checked_coords))

			# Check coordinate for shamblers in range of gaiaslimeoid.
			shambler_data = bknd_core.execute_sql_query(
				"SELECT {id_enemy}, {enemytype} FROM enemies WHERE {enemyclass} = %s AND {gvs_coord} IN %s AND {poi} = %s AND {id_server} = %s AND NOT ({life_state} = {life_state_dead} OR {life_state} = {life_state_unactivated})".format(
					id_enemy=ewcfg.col_id_enemy,
					enemyclass=ewcfg.col_enemy_class,
					enemytype=ewcfg.col_enemy_type,
					gvs_coord=ewcfg.col_enemy_gvs_coord,
					poi=ewcfg.col_poi,
					id_server=ewcfg.col_id_server,
					life_state=ewcfg.col_life_state,
					life_state_dead=ewcfg.enemy_lifestate_dead,
					life_state_unactivated=ewcfg.enemy_lifestate_unactivated,
				), (
					ewcfg.enemy_class_shambler,
					tuple(checked_coords),
					enemy_data.poi,
					enemy_data.id_server
				))

			# print(len(shambler_data))
			if len(shambler_data) > 0:

				for shambler in shambler_data:

					current_shambler_data = EwEnemy(id_enemy=shambler[0], id_server=enemy_data.id_server)
					detected_shamblers[current_shambler_data.id_enemy] = current_shambler_data.gvs_coord

					if shambler[1] in [ewcfg.enemy_type_juvieshambler] and current_shambler_data.enemy_props.get(
							'underground') == 'true':
						del detected_shamblers[current_shambler_data.id_enemy]

				if piercing == 'false':
					detected_shamblers = gvs_find_nearest_shambler(checked_coords, detected_shamblers)
				elif int(pierceamount) > 0:
					detected_shamblers = gvs_find_nearest_shambler(checked_coords, detected_shamblers, pierceamount,
																   singletilepierce)

			# print('gaia in coord {} found shambler in coords {} in {}.'.format(current_coord, checked_coords, enemy_data.poi))

			if splash == 'true':

				if detected_shamblers == {}:
					checked_splash_coords = checked_coords
				else:
					checked_splash_coords = []
					for shambler in detected_shamblers.keys():
						checked_splash_coords.append(detected_shamblers[shambler])

				splash_coords = gvs_get_splash_coords(checked_splash_coords)

				splash_shambler_data = bknd_core.execute_sql_query(
					"SELECT {id_enemy}, {enemytype}, {gvs_coord} FROM enemies WHERE {enemyclass} = %s AND {gvs_coord} IN %s AND {poi} = %s AND {id_server} = %s".format(
						id_enemy=ewcfg.col_id_enemy,
						enemyclass=ewcfg.col_enemy_class,
						enemytype=ewcfg.col_enemy_type,
						gvs_coord=ewcfg.col_enemy_gvs_coord,
						poi=ewcfg.col_poi,
						id_server=ewcfg.col_id_server,
					), (
						ewcfg.enemy_class_shambler,
						tuple(splash_coords),
						enemy_data.poi,
						enemy_data.id_server
					))

				for splashed_shambler in splash_shambler_data:
					detected_shamblers[splashed_shambler[0]] = splashed_shambler[2]
			break

	return detected_shamblers


def sh_check_coord_for_gaia(enemy_data, sh_range, direction):
	current_coord = enemy_data.gvs_coord
	gaias_in_coord = []

	if current_coord not in ewcfg.gvs_coords_end:

		for sh_row in ewcfg.gvs_valid_coords_shambler:

			if current_coord in sh_row:
				index = sh_row.index(current_coord)
				checked_coord = gvs_grid_gather_coords(enemy_data.enemyclass, sh_range, direction, sh_row, index)[0]

				for gaia_row in ewcfg.gvs_valid_coords_gaia:
					if checked_coord in gaia_row:
						# Check coordinate for gaiaslimeoids in front of the shambler.
						gaia_data = bknd_core.execute_sql_query(
							"SELECT {id_enemy}, {enemytype} FROM enemies WHERE {enemyclass} = %s AND {gvs_coord} = %s AND {poi} = %s AND {id_server} = %s AND NOT ({life_state} = {life_state_dead})".format(
								id_enemy=ewcfg.col_id_enemy,
								enemyclass=ewcfg.col_enemy_class,
								enemytype=ewcfg.col_enemy_type,
								gvs_coord=ewcfg.col_enemy_gvs_coord,
								poi=ewcfg.col_poi,
								id_server=ewcfg.col_id_server,
								life_state=ewcfg.col_life_state,
								life_state_dead=ewcfg.enemy_lifestate_dead,
							), (
								ewcfg.enemy_class_gaiaslimeoid,
								checked_coord,
								enemy_data.poi,
								enemy_data.id_server
							))

						# print(len(gaia_data))
						if len(gaia_data) > 0:

							low_attack_priority = [ewcfg.enemy_type_gaia_rustealeaves]
							high_attack_priority = [ewcfg.enemy_type_gaia_steelbeans]
							mid_attack_priority = []
							for enemy_id in ewcfg.gvs_enemies_gaiaslimeoids:
								if enemy_id not in low_attack_priority and enemy_id not in high_attack_priority:
									mid_attack_priority.append(enemy_id)

							gaia_types = {}
							for gaia in gaia_data:
								gaia_types[gaia[1]] = gaia[0]

							# Rustea Leaves only have a few opposing shamblers that can damage them
							if ewcfg.enemy_type_gaia_rustealeaves in gaia_types.keys() and enemy_data.enemytype not in [
								ewcfg.enemy_type_gigashambler, ewcfg.enemy_type_shambonidriver,
								ewcfg.enemy_type_ufoshambler]:
								del gaia_types[ewcfg.enemy_type_gaia_rustealeaves]

							for target in high_attack_priority:
								if target in gaia_types.keys():
									gaias_in_coord.append(gaia_types[target])

							for target in mid_attack_priority:
								if target in gaia_types.keys():
									gaias_in_coord.append(gaia_types[target])

							for target in low_attack_priority:
								if target in gaia_types.keys():
									gaias_in_coord.append(gaia_types[target])

					# print('shambler in coord {} found gaia in coord {} in {}.'.format(current_coord, checked_coord, enemy_data.poi))

	return gaias_in_coord


def gvs_grid_gather_coords(enemyclass, gr_range, direction, row, index):
	checked_coords = []

	if enemyclass == ewcfg.enemy_class_shambler:
		index_change = -2
		if direction == 'right':
			index_change *= -1

		try:
			checked_coords.append(row[index + index_change])
		except:
			pass

	else:

		index_changes = []

		# Default if range is 1, only reaches 0.5 and 1 full tile ahead
		for i in range(gr_range):
			index_changes.append(i + 1)

		# If it reaches backwards with a range of 1, reflect current index changes
		if direction == 'left':
			new_index_changes = []

			for change in index_changes:
				change *= -1
				new_index_changes.append(change)

			index_changes = new_index_changes

		# If it reaches both directions with a range of 1, add in opposite tiles.
		elif direction == 'frontandback':
			new_index_changes = []

			for change in index_changes:
				change *= -1
				new_index_changes.append(change)

			index_changes += new_index_changes

		# If it attacks in a ring formation around itself, there are no coord changes.
		# The proper coordinates will be fetched later as 'splash' damage.
		elif direction == 'ring':
			index_changes = [0]

		# Catch exceptions when necessary
		for index_change in index_changes:
			try:
				checked_coords.append(row[index + index_change])
			except:
				pass

	# print(index_changes)

	# print(gr_range)
	# print(checked_coords)
	# print(enemyclass)

	return checked_coords


def gvs_find_nearest_shambler(checked_coords, detected_shamblers, pierceamount=1, singletilepierce='false'):
	pierceattempts = 0
	current_dict = {}
	chosen_coord = ''

	for coord in checked_coords:
		for shambler in detected_shamblers.keys():
			if detected_shamblers[shambler] == coord:
				current_dict[shambler] = coord

				if singletilepierce == 'true':
					chosen_coord = coord
					for shambler in detected_shamblers.keys():
						if detected_shamblers[shambler] == chosen_coord:
							current_dict[shambler] = chosen_coord
						pierceattempts += 1
						if pierceattempts == pierceamount:
							return current_dict

			pierceattempts += 1
			if pierceattempts == pierceamount:
				return current_dict


def gvs_get_splash_coords(checked_splash_coords):
	# Grab any random coordinate from the supplied splash coordinates, then get the row that it's in.
	plucked_coord = checked_splash_coords[0]
	plucked_row = plucked_coord[0]
	top_row = None
	middle_row = None
	bottom_row = None

	extra_top_row = None  # Joybean Pawpaw
	extra_bottom_row = None  # Joybean Pawpaw
	row_range = 5  # Joybean Dankwheat = 9
	row_backpedal = 2  # Joybean Dankwheat = 4

	current_index = 0

	all_splash_coords = []
	if plucked_row == 'A':
		middle_row = 0
		bottom_row = 1
	elif plucked_row == 'B':
		top_row = 0
		middle_row = 1
		bottom_row = 2
	elif plucked_row == 'C':
		top_row = 1
		middle_row = 2
		bottom_row = 3
	elif plucked_row == 'D':
		top_row = 2
		middle_row = 3
		bottom_row = 4
	elif plucked_row == 'E':
		top_row = 3
		middle_row = 4

	for coord in checked_splash_coords:
		for sh_row in ewcfg.gvs_valid_coords_shambler:
			if coord in sh_row:
				current_index = sh_row.index(coord)
				break

		if top_row != None:
			for i in range(row_range):
				try:
					all_splash_coords.append(
						ewcfg.gvs_valid_coords_shambler[top_row][current_index - row_backpedal + i])
				except:
					pass
		if bottom_row != None:
			for i in range(row_range):
				try:
					all_splash_coords.append(
						ewcfg.gvs_valid_coords_shambler[bottom_row][current_index - row_backpedal + i])
				except:
					pass

		for i in range(row_range):
			try:
				all_splash_coords.append(ewcfg.gvs_valid_coords_shambler[middle_row][current_index - row_backpedal + i])
			except:
				pass

	return all_splash_coords

