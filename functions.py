#!/usr/bin/env python3

def addToBuffer(barcodeBuffer,barcode):

    for element in barcode:
        barcodeBuffer = barcodeBuffer + element
    return barcodeBuffer;
# -----------------------------------------------------------------------------------------
def checkBuffer(barcodeBuffer):

    if (len(barcodeBuffer) >= 16):
        valid = 1;
    else:
        valid = 0;

    return valid;
# -----------------------------------------------------------------------------------------
def AssignCodes(barcodeBuffer):
    #
    # Assign the barcodes independant of scan order using type iden (first check for trailer code)
    #

    # Check buffer length
    if (len(barcodeBuffer) != 16):
        print("")
        print("ERROR:")
        print("Invalid barcode(s) scanned.")
        print("ONLY 2 barcodes, with 8 characters each are accepted. Start over.")
        iden_codes = (1,0,0)    # Send an exit flag and return
        return iden_codes

    # Extract barcodes
    barcode1 = barcodeBuffer[:8]
    barcode2 = barcodeBuffer[8:]

    # Extract first 2 characters
    barcode1_type = barcode1[:2]
    barcode2_type = barcode2[:2]

    # Check first 2 characters & Assign types
    if barcode1_type == '10':
        trailer_code = barcode1;
        if barcode2_type == '00':
            action_code = barcode2;
        else:
            print("")
            print("ERROR:")
            print("Invalid/No action code was scanned. Start Over.")
            iden_codes = (1,0,0)    # Send an exit flag and return
            return iden_codes
       
    elif barcode2_type == '10':
        trailer_code = barcode2;
        if barcode1_type == '00':
            action_code = barcode1;
        else:
            print("")
            print("ERROR:")
            print("Invalid/No action code was scanned. Start Over.")
            iden_codes = (1,0,0)    # Send an exit flag and return
            return iden_codes

    else: # no trailer_id scanned
        print("")
        print("ERROR:")
        print("No Trailer code was scanned. Start Over.")
        iden_codes = (1,0,0)    # Send and exit code and return
        return iden_codes

    iden_codes = (0,trailer_code,action_code)    # Send a continue flag and return assigned barcode values

    return iden_codes
# -----------------------------------------------------------------------------------------
def QUERY_CheckTrailerExists(db, trailer_code):

    cursor = db.cursor()
    query = """SELECT EXISTS(SELECT * FROM trailers WHERE serial_num = %s);""" % (trailer_code)
    lines = cursor.execute(query)
    data = cursor.fetchall()

    for i in data:
        exists = i[0]

    return exists
# -----------------------------------------------------------------------------------------
def QUERY_InsertTrailer(db,trailer_code):

    #temp = []
    #temp2 = trailer_code[1:]        # remove the leading 2-digit idenifier code

    # Remove leading '0''s from remaing code (without iden code)
    #for i in temp2:
    #    while i == "0":
    #        i = i[1:]
    #        temp.append(i)

    #trailer_id = temp
    #print("trailer_id from code:", trailer_id)

    trailer_id = trailer_code[1:]

    cursor = db.cursor()
    query = """INSERT INTO trailers VALUES (%s, 1, NULL, %s,NULL);""" % (trailer_id, trailer_code)
    lines = cursor.execute(query)
    data = cursor.fetchall()

    return
# -----------------------------------------------------------------------------------------
def QUERY_TrailerID(db, trailer_barcode):

    cursor = db.cursor()
    query = """SELECT trailer_id FROM trailers WHERE serial_num = %s;""" % (trailer_barcode)
    lines = cursor.execute(query)
    data = cursor.fetchall()

    for i in data[0]:
        trailer_id = i

    return trailer_id

# -----------------------------------------------------------------------------------------
def QUERY_CheckStatusExists(db, trailer_id, state_id):

    cursor = db.cursor()
    query = """SELECT EXISTS(SELECT * FROM status WHERE trailer_id = %s AND state_id= %s);""" % (trailer_id, state_id)
    lines = cursor.execute(query)
    data = cursor.fetchall()

    for i in data:
        exists = i[0]

    return exists
# -----------------------------------------------------------------------------------------
def QUERY_InsertStatus(db,trailer_id,state_id):

    num_states = 29;        # TODO: could add a query here to find the number of items in the states table

    base = "INSERT INTO status VALUES "

    for i in range(1,num_states+1):
        if i == 1 or i == state_id:
            msg = "(%s, %s, 'T', NOW())" % (trailer_id,i)
        else:
            msg = "(%s, %s, 'F', NOW())" % (trailer_id,i)

        if not i == num_states:
            msg = msg + ","

        base = base + msg

    base = base + ";"
    
    #quotes = '""'
    #query = quotes + base + quotes
    
    cursor = db.cursor()
    query = """%s""" % base
    lines = cursor.execute(query)
    data = cursor.fetchall()
    
    return
# -----------------------------------------------------------------------------------------
def QUERY_UpdateStatus(db,trailer_id,state_id):

    cursor = db.cursor()
    query = """UPDATE status SET completed = 'T', timestamp = NOW() WHERE trailer_id = %s AND state_id = %s;""" % (trailer_id, state_id)
    lines = cursor.execute(query)
    data = cursor.fetchall()

    return
# -----------------------------------------------------------------------------------------
def QUERY_InsertBuildStatusDup(db,trailer_id,state_id):

    cursor = db.cursor()
    query = """INSERT INTO status VALUES (%s, %s, 'T', NOW());""" % (trailer_id, state_id)
    lines = cursor.execute(query)
    data = cursor.fetchall()
    
    return
# -----------------------------------------------------------------------------------------
def processBuffer(db, barcodeBuffer):
    #
    # Assumes that ONLY 2 codes are scanned in series.
    #

    # Extract, Identify, and Assign Barcodes to named variables
    iden_codes = AssignCodes(barcodeBuffer)
    # Check for valid codes
    exit_code = iden_codes[0]
    if exit_code:
        return
    else:
        trailer_code = iden_codes[1]
        action_code = iden_codes[2]    

    # Check if the trailer has been added to the system
    exists = QUERY_CheckTrailerExists(db, trailer_code)
    print("Trailer Exists?: ", exists)
    
    # Add trailer to db (if not already there)
    if not exists:
        QUERY_InsertTrailer(db,trailer_code)
        print("New Trialer detected... Added to the database.")
    
    # Use barcode to query trialer_id from db
    trailer_id = QUERY_TrailerID(db, trailer_code)
    print("trailer_id: ", trailer_id)

    # Extract state_id from action_code
    state_id = action_code[6:]
    print("state_id: ", state_id)
    #print('state_id_int: ', int(state_id))

    
    # Use trailer_id and state_id to check if value exsists in status table
    initialized = QUERY_CheckStatusExists(db, trailer_id, state_id)
    print("State & Trailer Combo Exist?: ", initialized)

    # Insert or update data (depending on existance)
    if initialized == 0:
        QUERY_InsertStatus(db,trailer_id,state_id)
    else:
        if int(state_id) >= 9 and int(state_id) <= 20:
            QUERY_InsertBuildStatusDup(db,trailer_id,state_id)
        else:
            QUERY_UpdateStatus(db,trailer_id,state_id)

    return; # end functions



