from ew.backend import core as bknd_core
from ew.backend.book import EwBook
from ew.static import cfg as ewcfg

readers = {}


# Unused
def bought_check(bought):
    if bought == 0:
        return False
    else:
        return True


# Unused
def check(str):
    if str.content.lower() == ewcfg.cmd_accept or str.content.lower() == ewcfg.cmd_refuse:
        return True


def get_page(id_book, page):
    book = EwBook(id_book=id_book)
    contents = book.book_pages.get(page, "")
    return contents


def int_is_zine(id_book = None, id_server = None, negative = False):
    direction = '>'
    if negative:
        direction = '<'
    book_list = []
    try:
        conn_info = bknd_core.databaseConnect()
        conn = conn_info.get('conn')
        cursor = conn.cursor()

        cursor.execute((
                "SELECT b.id_book " +
                "FROM books AS b " +
                "WHERE b.id_server = %s AND b.book_state {} 0 ".format(direction) +
                "ORDER BY b.id_book"
        ), (
            id_server,
        ))

        data = cursor.fetchall()
        if data != None:
            for row in data:
                book_list.append(row[0])
    finally:
        # Clean up the database handles.
        cursor.close()
        bknd_core.databaseClose(conn_info)
    if id_book in book_list:
        return True
    else:
        return False
