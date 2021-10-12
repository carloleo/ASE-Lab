from flakon import JsonBlueprint
from flask import abort, jsonify, request

from bedrock_a_party.classes.party import CannotPartyAloneError, Party, NotInvitedGuestError, ItemAlreadyInsertedByUser, NotExistingFoodError

parties = JsonBlueprint('parties', __name__)

_LOADED_PARTIES = {}  # dict of available parties
_PARTY_NUMBER = 0  # index of the last created party

'''
    require:
            must be called via either GET or POST
    brief: 
            create a party if called via POST 
            otherwise retrieves all parties if called via GET
    param: 
            guests: list of users who will attend to the party
'''
@parties.route("/parties", methods=['POST','GET'])
def all_parties():
    result = None
    if request.method == 'POST':
        try:
            #creating of a party
            result = create_party(request)
        except CannotPartyAloneError: #party must have guests
            abort(400, "Guests list cannot be empty")

    elif request.method == 'GET':
        #retrieving all parties
        result = get_all_parties()

    return result


'''
    require: 
            must be called  via GET
    brief:
            return loaded parties number 
'''
@parties.route("/parties/loaded", methods=['GET'])
def loaded_parties():
    size = len(_LOADED_PARTIES)
    return jsonify(loaded_parties = size)


'''
    require:
            must be called  via either GET or DELETE
            id must refer to an existing party
    brief: 
            retrieve a party if called via GET 
            delete a party if called via DELETE
    param:
            id: party id
'''
@parties.route("/party/<id>", methods=['GET','DELETE'])
def single_party(id):
    global _LOADED_PARTIES
    result = ""
    #verifying if id refers to an existing party
    exists_party(id)


    if 'GET' == request.method:
        #retrieving party and marshaling it into json format
        result = jsonify(_LOADED_PARTIES[id].serialize())

    elif 'DELETE' == request.method:
        #deleting party
        _LOADED_PARTIES.pop(id)

    return result


'''
    require: 
            must be called  via  GET 
            id must refer to an existing party
    brief:
            retrieve food list of a party
    param: 
            id: party id
'''
@parties.route("/party/<id>/foodlist",methods=['GET'] )
def get_foodlist(id):
    global _LOADED_PARTIES
    result = ""
    #verifying if id refers to an existing party
    exists_party(id)

    if 'GET' == request.method:
        #retrieving  food list
        food_list = _LOADED_PARTIES[id].get_food_list()
        #marshaling food list into js format 
        result = jsonify(foodlist = food_list.serialize())
   
    return result

"""
    require: 
              must be called via either POST or DELETE
              id must refer to an existing party
              user must be invited to the party
    brief: 
            add item to food list of a party if users is a guest and it is called via POST
            delete item to food list of a party if users is a guest and it is called via DELETE
    param:
            id: party id
            user: guest of party
            item: food to add
"""
@parties.route("/party/<id>/foodlist/<user>/<item>", methods=['POST','DELETE'])
def edit_foodlist(id, user, item):
    global _LOADED_PARTIES
    #verifying if id refers to an existing party
    exists_party(id)
    #retrieving party
    party = _LOADED_PARTIES[id]
    serialized_party = party.serialize()
    result = ""
    if 'POST' == request.method:
        try:
            #adding food to party list food 
            party.add_to_food_list(item,user)
            #preparing json response 
            result = jsonify(food=item,user=user)
        except NotInvitedGuestError:#to add an item user must be on guests list
            abort(401,user + " is not in the guest list")
        except ItemAlreadyInsertedByUser:
            abort(400,item + " already inserted in the food list")

    if 'DELETE' == request.method:
        try:
            #check if user is a guest
            if not user in serialized_party['guests']:
                abort(401)
            #removing item from party food list
            party.remove_from_food_list(item,user)
            result = jsonify(msg="Food deleted!")
        except NotExistingFoodError:
            abort(400,item + " does not exists in the food list")

    return result

#
# These are utility functions. Use them, DON'T CHANGE THEM!!
#

def create_party(req):
    global _LOADED_PARTIES, _PARTY_NUMBER

    # get data from request
    json_data = req.get_json()

    # list of guests
    try:
        guests = json_data['guests']
    except:
        raise CannotPartyAloneError("you cannot party alone!")

    # add party to the loaded parties lists
    _LOADED_PARTIES[str(_PARTY_NUMBER)] = Party(_PARTY_NUMBER, guests)
    _PARTY_NUMBER += 1

    return jsonify({'party_number': _PARTY_NUMBER - 1})


def get_all_parties():
    global _LOADED_PARTIES

    return jsonify(loaded_parties=[party.serialize() for party in _LOADED_PARTIES.values()])


def exists_party(_id):
    global _PARTY_NUMBER
    global _LOADED_PARTIES

    if int(_id) > _PARTY_NUMBER:
        abort(404)  # error 404: Not Found, i.e. wrong URL, resource does not exist
    elif not(_id in _LOADED_PARTIES):
        abort(410)  # error 410: Gone, i.e. it existed but it's not there anymore
