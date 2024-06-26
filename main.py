from flask import Flask, request, jsonify, render_template_string
import os, json, hashlib, secrets, string, time

app = Flask(__name__)

MAX_TIMESTAMP_OFFSET = 30
DATA_DIR = "Stored API Data/"
KEYS_DIR = "Stored API Keys/"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(KEYS_DIR):
    os.makedirs(KEYS_DIR)

def verify_hash(id, paramString, provided_hash):
    with open(os.path.join(KEYS_DIR,f"{id}.key"),'r') as f:
        local_key = f.read().strip()

    data_to_hash = local_key + paramString
    hash_object = hashlib.sha256(data_to_hash.encode())
    calculated_hash = hash_object.hexdigest()

    return calculated_hash == provided_hash

@app.route('/')
def user_interface():
    return render_template_string("<h1>This website is an API endpoint</h1>"), 404

@app.route('/getTimestamp')
def get_timestamp():
    return str(getTimestamp()),200
def getTimestamp():
    return int(time.time())

@app.route('/newID', methods=['GET'])
def new_id():
    # Generate a brand new hash key
    key_length = 32
    hash_key = ''.join(secrets.choice('abcdef' + string.digits) for _ in range(key_length))
    
    # Generate the ID by scanning all files and finding the first non-created id
    id = 0
    while True:
        filename = os.path.join(DATA_DIR, f"KEYVAL{id}.json")
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump({}, f)  # Initialize with an empty dictionary
            with open(os.path.join(KEYS_DIR, f"{id}.key"), 'w') as f:
                f.write(hash_key)
            break
        id += 1
    
    return jsonify({'id': id, 'hash_key': hash_key}), 200

@app.route('/editData', methods=['GET'])
def edit_data():
    id = request.args.get('id')
    key = request.args.get('key')
    val = request.args.get('val')
    timestamp = request.args.get('timestamp')
    provided_hash = request.args.get('hash')
    paramHashData = request.query_string.decode('utf-8')[:request.query_string.decode('utf-8').rfind('&')]

    if id==None or key==None or val==None or timestamp==None or provided_hash==None:
        return jsonify({'message': f'At least one parameter was missing from the request'}), 403

    data_file = os.path.join(DATA_DIR, f"KEYVAL{id}.json")
    if not os.path.exists(data_file):
        return jsonify({'message': f'ID {id} does not exist in the system yet'}), 403

    if abs(int(timestamp)-getTimestamp()) > MAX_TIMESTAMP_OFFSET:
        return jsonify({'message': f'The timestamp was too far out from the server time'}), 403
    
    if not verify_hash(id, paramHashData, provided_hash):
        return jsonify({'message': 'Hash verification failed'}), 403
    
    # Load existing data
    with open(data_file, 'r') as f:
        data = json.load(f)

    # Update data with new key-value pair
    data[key] = val

    # Save data to file
    with open(data_file, 'w') as f:
        json.dump(data, f)

    return jsonify({'message': 'Data updated successfully'}), 200

def isRestricted(x):
    x = x.lower()
    if "restrict" in x:
        return True
    if "private" in x:
        return True
    if "lock" in x:
        return True
    return False

@app.route('/getData', methods=['GET'])
def get_data():
    id = request.args.get('id')
    timestamp = request.args.get('timestamp')
    provided_hash = request.args.get('hash')
    paramHashData = request.query_string.decode('utf-8')[:request.query_string.decode('utf-8').rfind('&')]
    
    if id is None:
        all_data = {}
        for i in os.listdir(DATA_DIR):
            data_file = os.path.join(DATA_DIR, i)
            if data_file.endswith(".json"):
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    if "DataAccessLevel" not in data or not isRestricted(data["DataAccessLevel"]):
                        all_data[i] = data
        return jsonify(all_data), 200
    else:
        data_file = os.path.join(DATA_DIR, f"KEYVAL{id}.json")
        if not os.path.exists(data_file):
            return jsonify({'message': f'ID {id} does not exist in the system yet'}), 403
        
        with open(data_file, 'r') as f:
            data = json.load(f)
            if "DataAccessLevel" not in data or not isRestricted(data["DataAccessLevel"]):
                return jsonify(data), 200

        if timestamp is None or provided_hash is None:
            return jsonify({'message': f'This ID has set itself to private and at least one parameter was missing from the request'}), 403
        if not verify_hash(id, paramHashData, provided_hash):
            return jsonify({'message': f'This ID has set itself to private and hash verification failed'}), 403
        if abs(int(timestamp)-get_timestamp()) > MAX_TIMESTAMP_OFFSET:
            return jsonify({'message': f'This ID has set itself to private and the timestamp was too far out from the server time'}), 403
        return jsonify(data), 200

    return "Error", 404























if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80)
