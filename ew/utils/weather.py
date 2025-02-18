import asyncio
import random

from . import core as ewutils
from .combat import EwEnemy
from .combat import EwUser
from .district import EwDistrict
from .frontend import EwResponseContainer
from .slimeoid import EwSlimeoid
from ..backend import core as bknd_core
from ..backend import hunting as bknd_hunt
from ..backend import item as bknd_item
from ..backend.item import EwItem
from ..backend.market import EwMarket
from ..backend.player import EwPlayer
from ..static import cfg as ewcfg
from ..static import poi as poi_static
from ..static import weather as weather_static

"""
	Coroutine that continually calls weather_tick; is called once per server, and not just once globally
"""


async def weather_tick_loop(id_server):
    interval = ewcfg.weather_tick_length
    while not ewutils.TERMINATE:
        await asyncio.sleep(interval)
        await weather_tick(id_server=id_server)


""" Bleed slime for all users """


async def weather_tick(id_server = None):
    if id_server != None:
        try:
            market_data = EwMarket(id_server=id_server)
            
            if market_data.weather == ewcfg.weather_sunny:
                exposed_pois = []
                exposed_pois.extend(poi_static.capturable_districts)
                exposed_pois.extend(poi_static.outskirts)
                exposed_pois = tuple(exposed_pois)

                users = bknd_core.execute_sql_query(
                    "SELECT id_user FROM users WHERE id_server = %s AND {poi} IN %s AND {life_state} > 0".format(
                        poi=ewcfg.col_poi,
                        life_state=ewcfg.col_life_state
                    ), (
                        id_server,
                        exposed_pois

                    ))
                for user in users:
                    try:
                        user_data = EwUser(id_user=user[0], id_server=id_server)
                        if user_data.life_state == ewcfg.life_state_kingpin:
                            continue
                        else:
                            mutations = user_data.get_mutations()
                            if ewcfg.mutation_id_airlock in mutations:
                                user_data.hunger -= min(user_data.hunger, 5)
                    except:
                        ewutils.logMsg("Error occurred in weather tick for server {}".format(id_server))

            if market_data.weather != ewcfg.weather_bicarbonaterain:
                return

            exposed_pois = []
            exposed_pois.extend(poi_static.capturable_districts)
            exposed_pois.extend(poi_static.outskirts)
            exposed_pois = tuple(exposed_pois)

            client = ewutils.get_client()
            server = client.get_guild(id_server)

            users = bknd_core.execute_sql_query("SELECT id_user FROM users WHERE id_server = %s AND {poi} IN %s AND {life_state} > 0".format(
                poi=ewcfg.col_poi,
                life_state=ewcfg.col_life_state
            ), (
                id_server,
                exposed_pois

            ))

            deathreport = ""
            resp_cont = EwResponseContainer(id_server=id_server)
            for user in users:
                user_data = EwUser(id_user=user[0], id_server=id_server)
                if user_data.life_state == ewcfg.life_state_kingpin:
                    continue
                user_poi = poi_static.id_to_poi.get(user_data.poi)
                player_data = EwPlayer(id_server=user_data.id_server, id_user=user_data.id_user)

                protected = False
                slimeoid_protected = False

                if user_data.weapon >= 0:
                    weapon_item = EwItem(id_item=user_data.weapon)
                    if weapon_item.item_props.get('weapon_type') in ewcfg.rain_protection:
                        protected = True

                cosmetics = bknd_item.inventory(id_user=user_data.id_user, id_server=id_server, item_type_filter=ewcfg.it_cosmetic)

                for cosmetic in cosmetics:
                    cosmetic_data = EwItem(id_item=cosmetic.get('id_item'))
                    if cosmetic_data.item_props.get('id_cosmetic') in ewcfg.rain_protection:
                        if cosmetic_data.item_props.get('adorned') == 'true':
                            protected = True
                        elif cosmetic_data.item_props.get('slimeoid') == 'true':
                            slimeoid_protected = True

                if not protected:

                    if user_data.life_state == ewcfg.life_state_shambler:
                        slime_gain = (ewcfg.slimes_shambler - user_data.slimes) / 10
                        slime_gain = max(0, int(slime_gain))
                        user_data.change_slimes(n=slime_gain, source=ewcfg.source_weather)

                    else:
                        if random.random() < 0.01:
                            pass
                            #user_data.degradation += 1

                    user_data.persist()

                if not slimeoid_protected:
                    slimeoid_data = EwSlimeoid(id_user=user_data.id_user, id_server=id_server)

                    if slimeoid_data.life_state != ewcfg.slimeoid_state_active:
                        continue

                    slimeoid_response = ""
                    if random.randrange(10) < slimeoid_data.level:
                        slimeoid_response = "*{uname}*: {slname} cries out in pain, as it's hit by the bicarbonate rain.".format(uname=player_data.display_name, slname=slimeoid_data.name)

                    else:
                        item_props = {
                            'context': ewcfg.context_slimeoidheart,
                            'subcontext': slimeoid_data.id_slimeoid,
                            'item_name': "Heart of {}".format(slimeoid_data.name),
                            'item_desc': "A poudrin-like crystal. If you listen carefully you can hear something that sounds like a faint heartbeat."
                        }
                        bknd_item.item_create(
                            id_user=str(user_data.id_user),
                            id_server=id_server,
                            item_type=ewcfg.it_item,
                            item_props=item_props
                        )
                        slimeoid_data.die()
                        slimeoid_data.persist()
                        slimeoid_response = "*{uname}*: {slname} lets out a final whimper as it's dissolved by the bicarbonate rain. {skull} You quickly pocket its heart.".format(uname=player_data.display_name, slname=slimeoid_data.name, skull=ewcfg.emote_slimeskull)

                    resp_cont.add_channel_response(user_poi.channel, slimeoid_response)
            for poi in exposed_pois:
                district_data = EwDistrict(district=poi, id_server=id_server)
                slimes_to_erase = district_data.slimes * 0.01 * ewcfg.weather_tick_length
                slimes_to_erase = max(slimes_to_erase, ewcfg.weather_tick_length * 1000)
                slimes_to_erase = min(district_data.slimes, slimes_to_erase)

                # round up or down, randomly weighted
                remainder = slimes_to_erase - int(slimes_to_erase)
                if random.random() < remainder:
                    slimes_to_erase += 1
                slimes_to_erase = int(slimes_to_erase)

                district_data.change_slimes(n=- slimes_to_erase, source=ewcfg.source_weather)
                district_data.persist()

            enemies = bknd_core.execute_sql_query("SELECT id_enemy FROM enemies WHERE id_server = %s AND {poi} IN %s AND {life_state} = %s AND {weathertype} != %s".format(
                poi=ewcfg.col_enemy_poi,
                life_state=ewcfg.col_enemy_life_state,
                weathertype=ewcfg.col_enemy_weathertype
            ), (
                id_server,
                exposed_pois,
                ewcfg.enemy_lifestate_alive,
                ewcfg.enemy_weathertype_rainresist
            ))

            for enemy in enemies:
                enemy_data = EwEnemy(id_enemy=enemy[0])
                enemy_poi = poi_static.id_to_poi.get(enemy_data.poi)

                slimes_to_erase = enemy_data.slimes * 0.01 * ewcfg.weather_tick_length
                slimes_to_erase = max(slimes_to_erase, ewcfg.weather_tick_length * 1000)
                slimes_to_erase = min(enemy_data.slimes, slimes_to_erase)

                # round up or down, randomly weighted
                remainder = slimes_to_erase - int(slimes_to_erase)
                if random.random() < remainder:
                    slimes_to_erase += 1
                slimes_to_erase = int(slimes_to_erase)

                enemy_data.change_slimes(n=- slimes_to_erase, source=ewcfg.source_weather)
                enemy_data.persist()

                response = "{name} takes {slimeloss:,} damage from the bicarbonate rain.".format(name=enemy_data.display_name, slimeloss=slimes_to_erase)
                resp_cont.add_channel_response(enemy_poi.channel, response)
                if enemy_data.slimes <= 0:
                    bknd_hunt.delete_enemy(enemy_data)
                    deathreport = "{skull} {name} is dissolved by the bicarbonate rain. {skull}".format(skull=ewcfg.emote_slimeskull, name=enemy_data.display_name)
                    resp_cont.add_channel_response(enemy_poi.channel, deathreport)

            await resp_cont.post()

        except:
            ewutils.logMsg("Error occurred in weather tick for server {}".format(id_server))

async def weather_cycle(id_server = None):
    market_data = EwMarket(id_server)
    
    # Potentially change the weather
    if random.randrange(3) == 0:
            pattern_count = len(weather_static.weather_list)

            if pattern_count > 1:
                weather_old = market_data.weather

                # if random.random() < 0.4:
                # 	market_data.weather = ewcfg.weather_bicarbonaterain

                # Randomly select a new weather pattern. Try again if we get the same one we currently have.
                while market_data.weather == weather_old:
                    pick = random.randrange(len(weather_static.weather_list))
                    market_data.weather = weather_static.weather_list[pick].name
                    market_data.persist()
            # Log message for statistics tracking.
            ewutils.logMsg("The weather changed. It's now {}.".format(market_data.weather))