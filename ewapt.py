import asyncio

import random
import time

import ewcmd
import ewutils
from ewplayer import EwPlayer
import ewcfg
import ewrolemgr
import ewmarket
import ewitem
from ew import EwUser
import ewslimeoid
from ewmarket import EwMarket
import os
import discord
import discord.server

class EwApartment:
    id_user = ""
    id_server = ""

    name = "your city apartment."
    description = "It's drafty in here! You briefly consider moving out, but your SlimeCoin is desperate to leave your pocket."
    poi = "downtown"
    rent = 200000
    apt_class = 'c'

    def __init__(
            self,
            id_user=None,
            id_server=None
    ):
        if (id_user != None):
            self.id_user = id_user
            self.id_server = id_server

            try:
                conn_info = ewutils.databaseConnect()
                conn = conn_info.get('conn')
                cursor = conn.cursor()

                # Retrieve object
                cursor.execute("SELECT {}, {}, {}, {}, {}, {} FROM apartment WHERE id_user = %s".format(
                    ewcfg.col_id_server,
                    ewcfg.col_apt_name,
                    ewcfg.col_apt_description,
                    ewcfg.col_poi,
                    ewcfg.col_rent,
                    ewcfg.col_apt_class,

                    ewcfg.col_display_name
                ), (self.id_user,))
                result = cursor.fetchone();

                if result != None:
                    # Record found: apply the data to this object.
                    self.id_server = result[0]
                    self.name = result[1]
                    self.description = result[2]
                    self.poi = result[3]
                    self.rent = result[4]
                    self.apt_class = result[5]
                elif id_server != None:
                    # Create a new database entry if the object is missing.
                    cursor.execute("REPLACE INTO apartment({}, {}) VALUES(%s, %s)".format(
                        ewcfg.col_id_user,
                        ewcfg.col_id_server
                    ), (
                        self.id_user,
                        self.id_server
                    ))

                    conn.commit()
            finally:
                # Clean up the database handles.
                cursor.close()
                ewutils.databaseClose(conn_info)

    def persist(self):
        ewutils.execute_sql_query(
            "REPLACE INTO apartment ({col_id_server}, {col_id_user}, {col_apt_name}, {col_apt_description}, {col_poi}, {col_rent}, {col_apt_class}) VALUES (%s, %s, %s, %s, %s, %s, %s)".format(
                col_id_server=ewcfg.col_id_server,
                col_id_user=ewcfg.col_id_user,
                col_apt_name=ewcfg.col_apt_name,
                col_apt_description=ewcfg.col_apt_description,
                col_poi=ewcfg.col_poi,
                col_rent=ewcfg.col_rent,
                col_apt_class=ewcfg.col_apt_class
            ), (
                self.id_server,
                self.id_user,
                self.name,
                self.description,
                self.poi,
                self.rent,
                self.apt_class
            ))
class EwFurniture:
    item_type = "furniture"

    # The proper name of the cosmetic item
    id_furniture = ""

    # The string name of the cosmetic item
    str_name = ""

    # The text displayed when you look at it
    str_desc = ""

    # How rare the item is, can be "Plebeian", "Patrician", or "Princeps"
    rarity = ""

    # Cost in SlimeCoin to buy this item.
    price = 0

    # Names of the vendors selling this item.
    vendors = []

    #Text when placing the item
    furniture_place_desc = ""

    #Text when !look-ing at the item
    furniture_look_desc = ""

    #How you received this item
    acquisition = ""

    def __init__(
        self,
        id_furniture = "",
        str_name = "",
        str_desc = "",
        rarity = "",
        acquisition = "",
        price = 0,
        vendors = [],
        furniture_place_desc = "",
        furniture_look_desc = ""

    ):
        self.item_type = ewcfg.it_furniture
        self.id_furniture = id_furniture
        self.str_name = str_name
        self.str_desc = str_desc
        self.rarity = rarity
        self.acquisition = acquisition
        self.price = price
        self.vendors = vendors
        self.furniture_place_desc = furniture_place_desc
        self.furniture_look_desc = furniture_look_desc

async def consult(cmd):
    target_name = ewutils.flattenTokenListToString(cmd.tokens[1:])
    if target_name == None or len(target_name) == 0:
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "What region would you like to look at?"))
    user_data = EwUser(member=cmd.message.author)
    response = ""
    if user_data.poi != ewcfg.poi_id_realestate:
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "You have to !consult at Slimecorp Real Estate in Old New Yonkers."))
    poi = ewcfg.id_to_poi.get(target_name)
    if poi == None:
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "That place doesn't exist. The consultant behind the counter is aroused by your stupidity."))
    elif poi == ewcfg.poi_id_rowdyroughhouse or poi == ewcfg.poi_id_copkilltown or poi == ewcfg.poi_id_juviesrow:
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "\"We don't have apartments in such...urban places,\" your consultant mutters under his breath."))
    elif poi.is_subzone:
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "You don't find it on the list of properties. Try something that isn't a subzone."))
    elif poi.id_poi == ewcfg.poi_id_assaultflatsbeach:
        response = "This is Assault Flats Beach. There's dinosaurs, so we're charging all the legal fees to our tenants.\n\n"
        response +="The cost per month is {:,.2f} SC. \n\n The down payment is four times that, {:,.2f} SC.".format(6000000000*getPriceBase(cmd=cmd), 4*6000000000*getPriceBase(cmd=cmd))
    elif poi.id_poi == ewcfg.poi_id_dreadford:
        response = "This is Dreadford. There's golfing old people, so we're charging all the legal fees to our tenants.\n\n"
        response +="The cost per month is {:,.2f} SC. \n\n The down payment is four times that, {:,.2f} SC.".format(6000000000*getPriceBase(cmd=cmd), 4*6000000000*getPriceBase(cmd=cmd))
    elif poi.id_poi == ewcfg.poi_id_downtown:
        response = "This is Downtown. You need to be a big man if you're gonna take it downtown.\n\n"
        response +="The cost per month is {:,.2f} SC. \n\n The down payment is four times that, {:,.2f} SC.".format(3000000000*getPriceBase(cmd=cmd), 4*3000000000*getPriceBase(cmd=cmd))
    elif poi.property_class == "c":
        response = "This is a C class district. If you want to write flavor text for each zone you'll need a bunch of these elif statements.\n\n"
        response +="The cost per month is {:,.2f} SC. \n\n The down payment is four times that, {:,.2f} SC.".format(getPriceBase(cmd=cmd), 4*getPriceBase(cmd=cmd))
    elif poi.property_class == "b":
        response = "This is a B class district. These are placeholders, not intended to be in the game.\n\n"
        response +="The cost per month is {:,.2f} SC. \n\n The down payment is four times that, {:,.2f} SC.".format(1500*getPriceBase(cmd=cmd), 1500*4*getPriceBase(cmd=cmd))
    elif poi.property_class == "a":
        response = "This is an A class district. Based on existing code, the remaining statements should be easy.\n\n"
        response += "The cost per month is {:,.2f} SC. \n\n The down payment is four times that, {:,.2f} SC.".format(2000000 * getPriceBase(cmd=cmd), 2000000 * 4 * getPriceBase(cmd=cmd))
    else:
        response = "Not for sale."
    return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
async def signlease(cmd):
    target_name = ewutils.flattenTokenListToString(cmd.tokens[1:])
    if target_name == None or len(target_name) == 0:
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "What region would you like to rent?"))

    user_data = EwUser(member=cmd.message.author)
    user_apt = EwApartment(id_user = user_data.id_user, id_server = user_data.id_server)
    base_cost = 0;

    if user_data.poi != ewcfg.poi_id_realestate:
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "You have to !signlease at Slimecorp Real Estate in Old New Yonkers."))
    poi = ewcfg.id_to_poi.get(target_name)
    price = 0
    response = ""
    if poi == None:
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "That place doesn't exist. The consultant behind the counter is aroused by your stupidity."))
    elif poi == ewcfg.poi_id_rowdyroughhouse or poi == ewcfg.poi_id_copkilltown or poi == ewcfg.poi_id_juviesrow:
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "\"We don't have apartments in such...urban places,\" your consultant mutters under his breath."))
    elif poi.is_subzone:
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "You don't find it on the list of properties. Try something that isn't a subzone."))
    elif poi.id_poi == ewcfg.poi_id_assaultflatsbeach:
        base_cost = 6000000000 * getPriceBase(cmd=cmd)
    elif poi.id_poi == ewcfg.poi_id_dreadford:
        base_cost = 6000000000 * getPriceBase(cmd=cmd)
    elif poi.id_poi == ewcfg.poi_id_downtown:
        base_cost = 3000000000 * getPriceBase(cmd=cmd)
    elif poi.property_class == "c":
        base_cost = getPriceBase(cmd=cmd)
    elif poi.property_class == "b":
        base_cost = 1500 * getPriceBase(cmd=cmd)
    elif poi.property_class == "a":
        base_cost = 2000000 * getPriceBase(cmd=cmd)
    else:
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author,"Not for sale."))
    if(user_data.slimecoin < base_cost*4):
        return await ewutils.send_message(cmd.client, cmd.message.channel,ewutils.formatMessage(cmd.message.author, "You can't afford it."))

    user_data.change_slimecoin(n=-base_cost*4, coinsource=ewcfg.coinsource_spending)
    user_data.apt_zone = poi.id_poi
    user_data.persist()

    user_apt.name = "Slimecorp Apartment"
    user_apt.apt_class = poi.property_class
    user_apt.description = "You're on {}'s property.".format(cmd.message.author.display_name)
    user_apt.poi = poi.id_poi
    user_apt.rent = base_cost
    user_apt.persist()

    response = "You signed the lease for an apartment in {} for {:,.2f} SlimeCoin a month.".format(poi.str_name, base_cost)
    return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
async def retire(cmd):
    user_data = EwUser(member=cmd.message.author)
    poi = ewcfg.id_to_poi.get(user_data.poi)
    poi_dest = ewcfg.id_to_poi.get("apt")
    if user_data.apt_zone != poi.id_poi:
        response = "You don't own an apartment here."
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
    else:
        ewutils.moves_active[cmd.message.author.id] = 0
        await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "You enter your apartment."))
        await asyncio.sleep(20)
        user_data.poi = poi_dest.id_poi
        user_data.persist()
        await ewrolemgr.updateRoles(client=cmd.client, member=cmd.message.author)
        response = "You're in your apartment."
        await ewutils.send_message(cmd.client, cmd.message.author, response)


async def depart(cmd):
    player = EwPlayer(id_user = cmd.message.author.id)
    user_data = EwUser(id_user = player.id_user, id_server = player.id_server)
    ewutils.logMsg("{}".format(user_data.id_server))
    poi = ewcfg.id_to_poi.get("apt")
    poi_dest = ewcfg.id_to_poi.get(user_data.apt_zone)

    client = ewutils.get_client()
    server = ewcfg.server_list[user_data.id_server]
    member_object = server.get_member(player.id_user)

    if user_data.poi != "apt":
        response = "You're not in an apartment."
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
    else:
        ewutils.moves_active[cmd.message.author.id] = 0
        await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "You exit your apartment."))
        await asyncio.sleep(20)
        user_data.poi = poi_dest.id_poi
        user_data.persist()
        await ewrolemgr.updateRoles(client=client, member=member_object)
        response = "Here we are. The outside world."
        return await ewutils.send_message(cmd.client, ewutils.get_channel(server, poi_dest.channel), ewutils.formatMessage(cmd.message.author, response))

def getPriceBase(cmd):
    #based on stock success
    user_data = EwUser(member=cmd.message.author)
    kfc = ewmarket.EwStock(stock='kfc', id_server = user_data.id_server)
    tcb = ewmarket.EwStock(stock='tacobell', id_server=user_data.id_server)
    hut = ewmarket.EwStock(stock='pizzahut', id_server=user_data.id_server)
    return (kfc.market_rate+tcb.market_rate+hut.market_rate)*67
async def rent_time(id_server = None):
    if id_server != None:
        try:
            conn_info = ewutils.databaseConnect()
            conn = conn_info.get('conn')
            cursor = conn.cursor();
            client = ewutils.get_client()


            cursor.execute("SELECT apartment.rent, users.id_user FROM users INNER JOIN apartment ON users.id_user=apartment.id_user WHERE users.id_server = %s AND apartment.rent > 0".format(

            ), (
                id_server,
            ))

            landowners = cursor.fetchall()
            total_decayed = 0

            for landowner in landowners:
                user_data = EwUser(id_user=landowner[1], id_server=id_server)
                user_apt = EwApartment(id_user = landowner[1], id_server = id_server)
                if landowner[0] > user_data.slimecoin:
                    if(user_data.poi == ewcfg.poi_id_apt):
                        user_data.poi = user_data.apt_zone
                        server = ewcfg.server_list[user_data.id_server]
                        member_object = server.get_member(landowner[1])
                        await ewrolemgr.updateRoles(client = client, member=member_object)
                        poi = ewcfg.id_to_poi.get(user_data.apt_zone)
                        player = EwPlayer(id_user = landowner[1])
                        response = "{} just got evicted. Point and laugh, everyone.".format(player.display_name)
                        await ewutils.send_message(client, ewutils.get_channel(server, poi.channel), response)
                    user_data.apt_zone = "empty"
                    user_data.persist()
                    user_apt.rent = 0
                    user_apt.poi = " "
                    user_apt.persist()
                else:
                    user_data.change_slimecoin(n=-landowner[0], coinsource=ewcfg.coinsource_spending)
                    user_data.persist()
        finally:
            cursor.close()
            ewutils.databaseClose(conn_info)

async def rent_cycle(cmd):
    user_data = EwUser(member = cmd.message.author)
    await rent_time(id_server = user_data.id_server)

async def apt_look(cmd):
    playermodel = EwPlayer(id_user=cmd.message.author.id)
    apt_model = EwApartment(id_user=cmd.message.author.id, id_server=playermodel.id_server)
    print(apt_model.poi)
    poi = ewcfg.id_to_poi.get(apt_model.poi)
    response = "You stand in {}, your flat in {}.\n\n{}\n\n".format(apt_model.name, poi.str_name, apt_model.description)

    furns = ewitem.inventory(id_user= cmd.message.author.id+"furnish", id_server= playermodel.id_server, item_type_filter=ewcfg.it_furniture)
    for furn in furns:
        i = ewitem.EwItem(furn.get('id_item'))
        response += "{} ".format(i.item_props['furniture_look_desc'])
    response += " "
    iterate = 0
    frids = ewitem.inventory(id_user=cmd.message.author.id + "fridge", id_server=playermodel.id_server)
    if(len(frids) > 0):
        response += "Your fridge contains: "
        for frid in frids:
            if iterate == len(frids) - 1 and len(frids) > 1:
                response += "and "
            i = ewitem.EwItem(frid.get('id_item'))
            if i.item_type == ewcfg.it_food:
                response += "a {}, ".format(i.item_props['food_name'])
            elif i.item_type == ewcfg.it_weapon:
                response += "a {}, ".format(i.item_props['weapon_type'])
            elif i.item_type == ewcfg.it_cosmetic:
                response += "a {}, ".format(i.item_props['cosmetic_name'])
            elif i.item_type == ewcfg.it_medal:
                response += "a {}, ".format(i.item_props['medal_name'])
            elif i.item_type == ewcfg.it_questitem:
                response += "a {}, ".format(i.item_props['qitem_name'])
            elif i.item_type == ewcfg.it_furniture:
                response += "a {}, ".format(i.item_props['furniture_name'])
            elif i.item_type == ewcfg.it_item:
                response += "a {}, ".format(i.item_props['item_name'])
            else:
                response += "a thing, "
            iterate += 1
        response = response[:-2] + '.'
    closets = ewitem.inventory(id_user=cmd.message.author.id + "closet", id_server=playermodel.id_server)
    if (len(closets) > 0):
        response += " Your closet contains: "
        iterate = 0
        for closet in closets:
            if iterate == len(closets) - 1 and len(closets) > 1:
                response += "and "
            i = ewitem.EwItem(closet.get('id_item'))
            if i.item_type == ewcfg.it_food:
                response += "a {}, ".format(i.item_props['food_name'])
            elif i.item_type == ewcfg.it_weapon:
                response += "a {}, ".format(i.item_props['weapon_type'])
            elif i.item_type == ewcfg.it_cosmetic:
                response += "a {}, ".format(i.item_props['cosmetic_name'])
            elif i.item_type == ewcfg.it_medal:
                response += "a {}, ".format(i.item_props['medal_name'])
            elif i.item_type == ewcfg.it_questitem:
                response += "a {}, ".format(i.item_props['qitem_name'])
            elif i.item_type == ewcfg.it_furniture:
                response += "a {}, ".format(i.item_props['furniture_name'])
            elif i.item_type == ewcfg.it_item:
                response += "a {}, ".format(i.item_props['item_name'])
            else:
                response += "a thing, "
            iterate += 1
        response = response[:-2] + '.'
    return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def store_item(cmd, dest):
    destination = dest
    playermodel = EwPlayer(id_user=cmd.message.author.id)
    usermodel = EwUser(id_user=cmd.message.author.id, id_server=playermodel.id_server)
    apt_model = EwApartment(id_server=playermodel.id_server, id_user=cmd.message.author.id)
    item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
    item_sought = ewitem.find_item(item_search=item_search, id_user=cmd.message.author.id, id_server=playermodel.id_server)

    if item_sought:
        item = ewitem.EwItem(id_item=item_sought.get('id_item'))
        if item_sought.get('soulbound'):
            response = "You can't just put away soulbound items. You have to keep them in your pants at least until the Rapture hits."
            return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
        elif item_sought.get('item_type') == ewcfg.it_furniture and (dest != "furnish" and dest != "store"):
            response = "The fridge and closet don't have huge spaces for furniture storage. Try !furnish or !store instead."
            return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

        if destination == "store":
            if item_sought.get('item_type') == ewcfg.it_food:
                destination = "fridge"
            elif item_sought.get('item_type') == ewcfg.it_furniture:
                destination = "furnish"
            else:
                destination = "closet"

        fridge_limit = 4
        if apt_model.apt_class == "b":
            fridge_limit *= 2;
        elif apt_model.apt_class == "a":
            fridge_limit *= 3;
        elif apt_model.apt_class == "s":
            fridge_limit *= 5;

        if item_sought.get('item_type') == ewcfg.it_food:
            name_string = item.item_props['food_name']
        elif item_sought.get('item_type') == ewcfg.it_weapon:
            name_string = item.item_props['weapon_type']
        elif item_sought.get('item_type') == ewcfg.it_cosmetic:
            name_string = item.item_props['cosmetic_name']
            item.item_props['slimeoid'] = 'false'
            item.item_props["adorned"] = 'false'
            item.persist()
        elif item_sought.get('item_type') == ewcfg.it_medal:
            name_string = item.item_props['medal_name']
        elif item_sought.get('item_type') == ewcfg.it_questitem:
            name_string = item.item_props['qitem_name']
        elif item_sought.get('item_type') == ewcfg.it_furniture:
            name_string = item.item_props['furniture_name']
        elif item_sought.get('item_type') == ewcfg.it_item:
            name_string = item.item_props['item_name']
        else:
            name_string = "thing"


        items_stored = ewitem.inventory(id_user=cmd.message.author.id+destination, id_server=playermodel.id_server)
        if len(items_stored) >= fridge_limit * 2 and destination == "closet":
            response = "The closet is bursting at the seams. Fearing the consequences of opening the door, you decide to hold on to the {}.".format(name_string)
            return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
        elif len(items_stored) >= fridge_limit and destination == "fridge":
            response = "The fridge is so full it's half open, leaking 80's era CFCs into your flat. You decide to hold on to the {}.".format(name_string)
            return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
        elif len(items_stored) >= int(fridge_limit*1.5) and destination == "furnish":
            response = "You have a lot of furniture here already. Hoarding is unladylike, so you decide to hold on to the {}.".format(name_string)
            return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))


        if item_sought.get('item_type') == ewcfg.it_food and destination == "fridge" :
            item.item_props["time_fridged"] = time.time()
            item.persist()
        ewitem.give_item(id_item=item.id_item, id_server=playermodel.id_server, id_user=cmd.message.author.id + destination)
        if(destination == "furnish"):
            response = name_string = item.item_props['furniture_place_desc']
        else:
            response = "You store the {} in the {}.".format(name_string, destination)
    else:
        response = "Are you sure you have that item?."
    return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def remove_item(cmd, dest):
    destination = dest

    playermodel = EwPlayer(id_user=cmd.message.author.id)
    usermodel = EwUser(id_user=cmd.message.author.id, id_server=playermodel.id_server)
    apt_model = EwApartment(id_server=playermodel.id_server, id_user=cmd.message.author.id)

    item_search = ewutils.flattenTokenListToString(cmd.tokens[1:])
    if item_search == "slimeoid" and dest = store:
        await freeze(cmd)

    if dest == "apartment":
        item_sought = ewitem.find_item(item_search=item_search, id_user=cmd.message.author.id + "fridge", id_server=playermodel.id_server)
        if not item_sought:
            item_sought = ewitem.find_item(item_search=item_search, id_user=cmd.message.author.id + "closet", id_server=playermodel.id_server)
            if not item_sought:
                item_sought = ewitem.find_item(item_search=item_search, id_user=cmd.message.author.id + "furnish", id_server=playermodel.id_server)
    elif dest == "fridge":
        item_sought = ewitem.find_item(item_search=item_search, id_user=cmd.message.author.id + "fridge", id_server=playermodel.id_server)
    elif dest == "closet":
        item_sought = ewitem.find_item(item_search=item_search, id_user=cmd.message.author.id + "closet", id_server=playermodel.id_server)
    elif dest == "furnish":
        item_sought = ewitem.find_item(item_search=item_search, id_user=cmd.message.author.id + "furnish", id_server=playermodel.id_server)

    name_string = ""
    if item_sought:
        item = ewitem.EwItem(id_item=item_sought.get('id_item'))

        if item_sought.get('item_type') == ewcfg.it_food:
            name_string = item.item_props['food_name']
        elif item_sought.get('item_type') == ewcfg.it_weapon:
            name_string = item.item_props['weapon_name']
        elif item_sought.get('item_type') == ewcfg.it_cosmetic:
            name_string = item.item_props['cosmetic_name']
            item.item_props["adorned"] = 'false'
            item.persist()
        elif item_sought.get('item_type') == ewcfg.it_medal:
            name_string = item.item_props['medal_name']
        elif item_sought.get('item_type') == ewcfg.it_questitem:
            name_string = item.item_props['qitem_name']
        elif item_sought.get('item_type') == ewcfg.it_furniture:
            name_string = item.item_props['furniture_name']
        elif item_sought.get('item_type') == ewcfg.it_item:
            name_string = item.item_props['item_name']
        else:
            name_string = "thing"


        if item_sought.get('item_type') == ewcfg.it_food and destination == "fridge":
            print(item.item_props.get("time_fridged"))
            item.item_props['time_expir'] = str(int(item.item_props.get('time_expir')) + (int(time.time())-int(item.item_props.get('time_fridged'))))
            item.item_props['time_fridged'] = '0'
            item.persist()
        ewitem.give_item(id_item=item.id_item, id_server=playermodel.id_server, id_user=cmd.message.author.id)
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "You take the {} from your {}.".format(name_string, destination)))
    else:
        response = "Are you sure you have that item?."
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def upgrade(cmd):
    playermodel = EwPlayer(id_user=cmd.message.author.id)
    usermodel = EwUser(id_user=cmd.message.author.id, id_server=playermodel.id_server)
    apt_model = EwApartment(id_server=playermodel.id_server, id_user=cmd.message.author.id)

    if(usermodel.poi != ewcfg.poi_id_realestate):
        response = "Upgrade your home at the apartment agency."
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
    elif(apt_model.apt_class == 's'):
        response = "Fucking hell, man. You're loaded, and we're not upgrading you."
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
    elif(usermodel.slimecoin < apt_model.rent*8):
        response = "You can't even afford the down payment. We're not entrusting an upgrade to a 99%er like you."
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
    else:
        response = "Are you sure? The upgrade cost is {} SC, and rent goes up to {} SC per month. To you !accept the deal, or do you !refuse it?".format(apt_model.rent*8, apt_model.rent*2)
        await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
        accepted = False

        try:
            message = await cmd.client.wait_for_message(timeout=30, author=cmd.message.author, check=ewslimeoid.check)

            if message != None:
                if message.content.lower() == "!accept":
                    accepted = True
                if message.content.lower() == "!refuse":
                    accepted = False
        except:
            accepted = False
        if not accepted:
            response = "Eh. Your loss."
            return await ewutils.send_message(cmd.client, cmd.message.channel,ewutils.formatMessage(cmd.message.author, response))
        else:
            usermodel.change_slimecoin(n=apt_model.rent * -8, coinsource= ewcfg.coinsource_spending)
            apt_model.rent *= 2
            letter = apt_model.apt_class
            if letter == 'a':
                letter = 's'
            elif letter == 'b':
                letter = 'a'
            elif letter == 'c':
                letter = 'b'
            apt_model.apt_class = letter
            usermodel.persist()
            apt_model.persist()
            response = "The deed is done. Back at your apartment, a Slimecorp builder nearly has a stroke trying to speed-renovate. You're now rank {}.".format(letter)
            return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def bazaar_update(cmd):
    playermodel = EwPlayer(id_user=cmd.message.author.id)
    market_data = EwMarket(playermodel.id_server)
    market_data.bazaar_wares.clear()

    bazaar_foods = []
    bazaar_cosmetics = []
    bazaar_general_items = []
    bazaar_furniture = []

    for item in ewcfg.vendor_inv.get(ewcfg.vendor_bazaar):
        if item in ewcfg.item_names:
            bazaar_general_items.append(item)

        elif item in ewcfg.food_names:
            bazaar_foods.append(item)

        elif item in ewcfg.cosmetic_names:
            bazaar_cosmetics.append(item)

        elif item in ewcfg.furniture_names:
            bazaar_furniture.append(item)

    market_data.bazaar_wares['generalitem'] = random.choice(bazaar_general_items)

    market_data.bazaar_wares['food1'] = random.choice(bazaar_foods)
    # Don't add repeated foods
    while market_data.bazaar_wares.get('food2') is None or market_data.bazaar_wares.get('food2') == \
            market_data.bazaar_wares['food1']:
        market_data.bazaar_wares['food2'] = random.choice(bazaar_foods)

    market_data.bazaar_wares['cosmetic1'] = random.choice(bazaar_cosmetics)
    # Don't add repeated cosmetics
    while market_data.bazaar_wares.get('cosmetic2') is None or market_data.bazaar_wares.get('cosmetic2') == \
            market_data.bazaar_wares['cosmetic1']:
        market_data.bazaar_wares['cosmetic2'] = random.choice(bazaar_cosmetics)
    while market_data.bazaar_wares.get('cosmetic3') is None or market_data.bazaar_wares.get('cosmetic3') == \
            market_data.bazaar_wares['cosmetic1'] or market_data.bazaar_wares.get('cosmetic3') == \
            market_data.bazaar_wares['cosmetic2']:
        market_data.bazaar_wares['cosmetic3'] = random.choice(bazaar_cosmetics)

    market_data.bazaar_wares['furniture1'] = random.choice(bazaar_furniture)


    market_data.persist()
async def freeze(cmd):

    return

async def apartment (cmd):
    usermodel = EwUser(member=cmd.message.author)
    poi = ewcfg.id_to_poi.get(usermodel.poi)
    response = "Your apartment is in {}.".format(poi.str_name)
    return await ewutils.send_message(cmd.client, cmd.message.channel,ewutils.formatMessage(cmd.message.author, response))


async def aptCommands(cmd):
    playermodel = EwPlayer(id_user=cmd.message.author.id)
    usermodel = EwUser(id_user=cmd.message.author.id, id_server=playermodel.id_server)
    tokens_count = len(cmd.tokens)
    cmd_text = cmd.tokens[0].lower() if tokens_count >= 1 else ""
    if cmd_text == ewcfg.cmd_depart:
        return await depart(cmd)
    elif cmd_text == ewcfg.cmd_fridge:
        await store_item(cmd=cmd, dest="fridge")
    elif cmd_text == ewcfg.cmd_store:
        await store_item(cmd=cmd, dest="store")
    elif cmd_text == ewcfg.cmd_closet:
        await store_item(cmd=cmd, dest="closet")
    elif cmd_text == ewcfg.cmd_take:
        await remove_item(cmd=cmd, dest="apartment")
    elif cmd_text == ewcfg.cmd_uncloset:
        await remove_item(cmd=cmd, dest="closet")
    elif cmd_text == ewcfg.cmd_unfridge:
        await remove_item(cmd=cmd, dest="fridge")
    elif cmd_text == ewcfg.cmd_furnish:
        await store_item(cmd=cmd, dest="furnish")
    elif cmd_text == ewcfg.cmd_unfurnish:
        await remove_item(cmd=cmd, dest="furnish")
    elif cmd_text == ewcfg.cmd_look:
        return await apt_look(cmd)
    elif cmd_text == "!bazaarupdate":
        return await bazaar_update(cmd)
    else:
        return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, "ENDLESS WAR denies you this favor."))