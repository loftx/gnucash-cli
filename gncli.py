#!/usr/bin/python

'''

gnucash_rest.py -- A Flask app which responds to REST requests
with JSON responses

Copyright (C) 2013 Tom Lofts <dev@loftx.co.uk>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of
the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, contact:

Free Software Foundation Voice: +1-617-542-5942
51 Franklin Street, Fifth Floor Fax: +1-617-542-2652
Boston, MA 02110-1301, USA gnu@gnu.org

@author Tom Lofts <dev@loftx.co.uk>

'''

import sys, getopt
import re
import gnucash

from decimal import Decimal

from gnucash.gnucash_business import Vendor, Bill, Entry, GncNumeric, \
    Customer, Invoice, Split, Account, Transaction

from gnucash.gnucash_business import \
    GNC_AMT_TYPE_VALUE, \
    GNC_AMT_TYPE_PERCENT

from gnucash import \
    QOF_QUERY_AND, \
    QOF_QUERY_OR, \
    QOF_QUERY_NAND, \
    QOF_QUERY_NOR, \
    QOF_QUERY_XOR

from gnucash import \
    QOF_STRING_MATCH_NORMAL, \
    QOF_STRING_MATCH_CASEINSENSITIVE

from gnucash import \
    QOF_COMPARE_LT, \
    QOF_COMPARE_LTE, \
    QOF_COMPARE_EQUAL, \
    QOF_COMPARE_GT, \
    QOF_COMPARE_GTE, \
    QOF_COMPARE_NEQ

from gnucash import \
    INVOICE_TYPE

from gnucash import \
    INVOICE_IS_PAID
   
from gnucash.gnucash_core_c import \
    GNC_INVOICE_CUST_INVOICE, \
    GNC_INVOICE_VEND_INVOICE, \
    INVOICE_IS_POSTED

# define globals for compatiblity with Gnucash rest
session = None

def start_session(connection_string, is_new, ignore_lock):

    global session

    # If no parameters are supplied attempt to use the app.connection_string if one exists
    if connection_string == '' and is_new == '' and  ignore_lock == '' and hasattr(app, 'connection_string') and app.connection_string != '':
        is_new = False
        ignore_lock = False
        connection_string = app.connection_string

    if connection_string == '':
        raise Error('InvalidConnectionString', 'A connection string must be supplied',
            {'field': 'connection_string'})

    if str(is_new).lower() in ['true', '1', 't', 'y', 'yes']:
        is_new = True
    elif str(is_new).lower() in ['false', '0', 'f', 'n', 'no']:
        is_new = False
    else:
        raise Error('InvalidIsNew', 'is_new must be true or false',
            {'field': 'is_new'})

    if str(ignore_lock).lower() in ['true', '1', 't', 'y', 'yes']:
        ignore_lock = True
    elif str(ignore_lock).lower() in ['false', '0', 'f', 'n', 'no']:
        ignore_lock = False
    else:
        raise Error('InvalidIgnoreLock', 'ignore_lock must be true or false',
            {'field': 'ignore_lock'})

    if session is not None:
        raise Error('SessionExists',
            'The session already exists',
            {})

    try:
        session = gnucash.Session(connection_string, is_new=is_new, ignore_lock=ignore_lock)
    except gnucash.GnuCashBackendException as e:
        raise Error('GnuCashBackendException',
            'There was an error starting the session',
            {
                'message': e.args[0],
                'code': parse_gnucash_backend_exception(e.args[0])
            })

    return session

def end_session():

    global session

    if session == None:
        raise Error('SessionDoesNotExist',
            'The session does not exist',
            {})

    try:
        session.save()
    except gnucash.GnuCashBackendException as e:
        raise Error('GnuCashBackendException',
            'There was an error saving the session',
            {
                'message': e.args[0],
                'code': parse_gnucash_backend_exception(e.args[0])
            })

    session.end()
    session.destroy()

    session = None

def parse_gnucash_backend_exception(exception_string):
    # Argument is of the form "call to %s resulted in the following errors, %s" - extract the second string
    reresult = re.match(r'^call to (.*?) resulted in the following errors, (.*?)$', exception_string)
    if len(reresult.groups()) == 2:
        return reresult.group(2)
    else:
        return ''

def sint(s):
    try:
        return int(s)
    except ValueError:
        return None

def gnc_numeric_from_decimal(decimal_value):
    sign, digits, exponent = decimal_value.as_tuple()

    # convert decimal digits to a fractional numerator
    # equivlent to
    # numerator = int(''.join(digits))
    # but without the wated conversion to string and back,
    # this is probably the same algorithm int() uses
    numerator = 0
    TEN = int(Decimal(0).radix()) # this is always 10
    numerator_place_value = 1
    # add each digit to the final value multiplied by the place value
    # from least significant to most sigificant
    for i in range(len(digits)-1,-1,-1):
        numerator += digits[i] * numerator_place_value
        numerator_place_value *= TEN

    if decimal_value.is_signed():
        numerator = -numerator

    # if the exponent is negative, we use it to set the denominator
    if exponent < 0 :
        denominator = TEN ** (-exponent)
    # if the exponent isn't negative, we bump up the numerator
    # and set the denominator to 1
    else:
        numerator *= TEN ** exponent
        denominator = 1

    return GncNumeric(numerator, denominator)

class Error(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, type, message, data):
        self.type = type
        self.message = message
        self.data = data


if __name__ == "__main__":

    arguments = sys.argv[1:]

    if len(arguments) == 0:
        print 'Usage: gncli.py <type> <command> <file or connection string>'
        sys.exit(2)

    type = arguments[0]
    command = arguments[1]
    connection_string = arguments[2]

    if type == 'book':
        if command == 'new':
            
            try:
                start_session(connection_string, True, False)
                end_session()
            except Error as error:
                print error.message
                sys.exit(2)

            print 'New book created'

        else:
            print 'Command not found'  


    else:
        print 'Type not found'
