#!/usr/bin/env python3

"""
    Upload consensus sequences and metadata to GISAID.
    Copyright (C) 2023 Friends of GISAID.
"""


import getpass, sys, requests, secrets, hashlib, json, time, csv, os
from itertools import islice
from epiflu_cli.utils import __st__
from epiflu_cli.utils.dates_checker import formatdate


# global configuration
GPS_SERVICE_URL_TEST = "https://gpsapi-test.epicov.org/epi3/gps_api"
GPS_SERVICE_URL_LOCAL = "http://localhost:8080/epi3/gps_api"
GPS_SERVICE_URL = "https://gpsapi.epicov.org/epi3/gps_api"
TAB = "\t"
DATABASE = 'flu'
def get_service_url(client_type):
    """Get service url."""
    if client_type == "test":
        return GPS_SERVICE_URL_TEST
    elif client_type == "local":
        return GPS_SERVICE_URL_LOCAL
    else:
        return GPS_SERVICE_URL


def call_api(params, proxy, debug, client_type):
    """ call the GPS-API """
    body = json.dumps(params)
    try:
        r = requests.post(get_service_url(client_type),
                          data=body,
                          proxies=proxy)
        time.sleep(0.1)
        return r.json()
    except requests.exceptions.ProxyError:
        if debug:
            raise
        else:
            return {"rc": "proxy_error"}
    except KeyboardInterrupt:
        raise
    except:
        if debug:
            raise
        else:
            return {"rc": "connection_error"}

def sha512_hexdigest(inp):
    """Create sha512"""
    hasher = hashlib.sha512()
    hasher.update(inp)
    return hasher.hexdigest()

def request_authentication_token(ctx, client_id, user, password, proxy, debug, client_type):
    """
    Request authentication token from GISAID GPS-API.
    Used only for the `authenticate` sub-command (since >=v2.0.1)
    """
    password = password.encode("utf8")
    salt = secrets.token_urlsafe(64)
    hashed = salt + "/" + sha512_hexdigest((salt + sha512_hexdigest(password)).encode("ascii"))

    # resp is response
    resp = call_api({"cmd": "state/auth/get_token",
                     "api": {"version": 1},
                     "ctx": ctx,
                     "client_id": client_id,
                     "login": user,
                     "hash": hashed},
                    proxy,
                    debug,
                    client_type)

    return resp["rc"], resp.get("auth_token"), resp.get("valid_until")


def write_authentication_token_file(ctx, filename, client_id, token, valid_until):
    """
    Write the authentication token.
    """
    tokens = {}
    tokens[ctx] = {'client-id': client_id,
                        'token': token,
                        'expiry': valid_until,
                       }
    with open(filename, "w") as file:
        file.write(json.dumps(tokens))
    return tokens

def load_authentication_token(ctx, filename, debug):
    """Load the authentication token."""
    try:
        with open(filename, "r") as file:
            return json.loads(file.read())[ctx] # get the row out of json *.authtoken file
    except:
        if debug:
            raise
        else:
            sys.exit(f"Unable to process file '{filename}' for {ctx}. Re-run `epiflu_cli authenticate`")

def parse_csv(filename):
    """Parse a csv file."""
    file = open(filename, "r", encoding="utf-8-sig")
    return csv.DictReader(file, delimiter=",", quotechar="\"")

def parse_fasta(fn):
    """
    >>> import tempfile
    >>> with tempfile.NamedTemporaryFile() as tmp:
    ...    tmp.write(b'''>EPI_ISL_8747624786432768.1
    ...    ACGACCTAACTGAGGA
    ...    ACACCTAACTGAGAGA''')
    ...    tmp.seek(0)
    ...    sequences = {header: sequence for header, sequence in parse_fasta(tmp.name)}
    ...    print(sequences)
    67
    0
    {'EPI_ISL_8747624786432768.1': 'ACGACCTAACTGAGGAACACCTAACTGAGAGA'}

    """


    seq = None
    header = None
    for row in open(fn, "r", encoding="utf-8-sig"):
        row = row.strip()
        if row:
            if row[0] == ">":
                if seq:
                    yield header, "".join(seq)
                header = row[1:].lstrip()
                seq = []
            else:
                if ">" in row:
                    raise ValueError("Found '>' in sequence-data")
                seq.append(row)
    if seq:
        yield header, "".join(seq)


def split_every(n, iterable):
    """Split iterable into n-sized chunks."""
    iterable = iter(iterable)
    yield from iter(lambda: list(islice(iterable, n)), [])


def get_sequence_references(submission):
    """
    Flu has multiple segments in a single sample submission.
    This function pulls out the segments and labels them
    with the cleaned name stored in sequence_reference_fields.
    """
    sequence_reference_fields = {"Seq_Id (HA)": "Seq_HA",
                                 "Seq_Id (NA)": "Seq_NA",
                                 "Seq_Id (PB1)": "Seq_PB1",
                                 "Seq_Id (PB2)": "Seq_PB2",
                                 "Seq_Id (PA)": "Seq_PA",
                                 "Seq_Id (MP)": "Seq_MP",
                                 "Seq_Id (NS)": "Seq_NS",
                                 "Seq_Id (NP)": "Seq_NP",
                                 "Seq_Id (HE)": "Seq_HE",
                                 "Seq_Id (P3)": "Seq_P3"}
    out = {}
    for key, alias in sequence_reference_fields.items():
        if submission.get(key):
            out[alias] = submission[key]            
    return out


def handle(args):
    """
    Handle execution of the workflow:
        authenticate
        upload
        labs
    """
    database = DATABASE
    proxy = None
    if any(label in args.subparser_name for label in ["authenticate", "labs", "upload"]) and args.proxy:
        # print("entered proxy")
        proxy = {"https": args.proxy,
                 "http": args.proxy}
        # print(f"proxy settings: {proxy}")
    client_type = 'live'

    def log(code, *msg):
        """
        Write to stdout and, to file for future reference.
        """
        with open(args.log, "a") as f:
            output = f"{code}: {', '.join(msg)}"
            f.write(output + os.linesep)
            print(output)


    # FLU-API: dump JSON-messages here
    def output_faulty(resp, submission):
        if "validation" in resp:
            log("validation_error", "%s" % submission.get("Isolate_Name"),
                resp["rc"], json.dumps(resp["validation"]))
        else:
            log("upload_error", "%s; %s" % (submission.get("Isolate_Name"), resp["rc"]))


    # execute CLI-commands
    if args.subparser_name == "authenticate":
        from pathlib import PurePath, Path
        if args.force and Path(args.token).exists():
            print(f"Will overwrite '{Path(args.token)}'.")
        elif (args.force and not Path(args.token).exists()) or \
            (not args.force and not Path(args.token).exists()):
            print(f"Will write authentication token to '{Path(args.token)}'")
        else:
            sys.exit(f"'{args.token}' already exists and force overwrite is off, so doing nothing.")
        if not args.username:
            args.username = getpass.getpass("Enter username: ")
        if not args.password:
            args.password = getpass.getpass("Enter password: ")
        if not args.client_id:
            args.client_id = getpass.getpass("Enter client-ID: ")

        if args.client_id.startswith("TEST-"):
            client_type = "test"
        elif args.client_id.startswith("LOCAL-"):
            client_type = "local"

        rc, auth_token, valid_until = request_authentication_token(ctx=database,
                                                                   client_id=args.client_id,
                                                                   user=args.username,
                                                                   password=args.password,
                                                                   proxy=proxy,
                                                                   debug=args.debug,
                                                                   client_type=client_type)
        # print(rc, auth_token, valid_until)
        if rc == "ok":
            log("\nok", "user authenticated")
            log("valid until", time.ctime(valid_until))
        else:
            log("Response from server:", rc)

        # save it or report error
        if auth_token:
            write_authentication_token_file(database, args.token, args.client_id,
                                            auth_token, time.ctime(valid_until))
            return 0
        else:
            return 1

    elif args.subparser_name == "upload":
        auth_token = load_authentication_token(database, args.token, args.debug)
        client_id = auth_token['client-id']
        auth_token = auth_token['token']

        if client_id.startswith("TEST-"):
            client_type = "test"
        elif client_id.startswith("LOCAL-"):
            client_type = "local"

        # FLU-API-CHANGES: we have to support multiple endpoints here: FLU has it's own
        # get cmd from database context
        cmd = "data/flu/upload"
        metadata = parse_csv(args.metadata)
        # parse FASTA
        try:
            sequences = {header: sequence for header, 
                         sequence in parse_fasta(args.fasta)}
        except ValueError:
            log("fasta_format_error", "upload aborted")
            return 1

        # check for completeness by comparing fasta and metadata
        submissions = []
        missing_data = False
        for row in metadata:
            submission = dict(row)
            sequence_references = get_sequence_references(submission)

            submission['Collection_Date'] = str(formatdate(row. \
                                                get('Collection_Date'),
                                                args.dateformat))

            for field_name, seq_id in sequence_references.items():
                if seq_id not in sequences:
                    log("missing_seq", "missing sequence '" + seq_id + "'")
                    missing_data = True

            submission["segments"] = {}
            submission["submitter"] = None
            for field_name, seq_id in sequence_references.items():
                if seq_id not in sequences:
                    log("missing_seq", "missing sequence '" + seq_id + "'")
                    missing_data = True
                else:
                    submission["segments"][field_name] = sequences[seq_id]
            submissions.append(submission)

        if missing_data:
            log("missing_data", "upload failed")
            return 1

        # FLU-API-CHANGES: the FLU-API must be fed with mutliple submissions at
        # once, this is triggered by "send_in_one_packet" and "batch_size"
        batch_size = 50
        send_in_one_packet = True

        submission_chunks = split_every(batch_size, submissions)
        count = 0
        ok_count = 0
        message_count = 0

        for submission_chunk in submission_chunks: # to stop overload on curation, blocks of 500.
            # logon = open session
            # print(submission_chunk)
            resp = call_api({"cmd": "state/session/logon", #cmd is logon
                             "api": {"version": 1},
                             "client_id": client_id,
                             "auth_token": auth_token},
                            proxy,
                            debug=args.debug,
                            client_type=client_type)

            time.sleep(0.5) # give system time to save session

            if resp["rc"] == "auth_token_invalid":
                log("invalid_token", "invalid auth-token")
                return 1
            elif resp["rc"] != "ok":
                log("error", "unexpected response from GPS-API", repr(resp))
                return 1

            sid = resp["sid"]

            # do uploads
            packet = []
            for submission in submission_chunk:
                submitter = submission["submitter"]
                virus_name_key = None
                if "Isolate_Name" in submission:
                    virus_name_key = "Isolate_Name"
                    # sequence_key = ""
                else:
                    # ""
                    log("missing_virus_name", f"{submission}")
                # print(virus_name_key)
                if send_in_one_packet:
                    # FLU-API-CHANGES: only collect the submission into the list "packet"
                    packet.append(submission)
                else:
                    resp = call_api({"cmd": "data/hcov-19/upload", #cmd is upload
                                     "api": {"version": 1},
                                     "sid": sid,
                                     "data": submission,
                                     "submitter": submitter,
                                     },
                                    proxy,
                                    debug=args.debug,
                                    client_type=client_type)
                    if resp["rc"] == "ok":
                        ok_count += 1
                        log("epi_isl_id", f"{submission.get(virus_name_key,'')}; {resp['accession_id']}")
                    else:
                        output_faulty(resp, submission)
                        # if "validation" in resp:
                        #     log("validation_error", "%s; %s; %s" % (submission.get(virus_name_key, ""), resp["rc"], json.dumps(resp["validation"])))
                        # else:
                        #     log("upload_error", "%s; %s" % (submission.get(virus_name_key, ""), resp["rc"])) #resp["rc"]
                    count += 1
            # print(packet)
            # print(send_in_one_packet)

            if send_in_one_packet:
                # FLU-API-CHANGES: when collected "batch_size" submissions in list "packet", send it to the API
                resp = call_api({"cmd": cmd,
                                 "api": {"version": 1},
                                 "sid": sid,
                                 "data": packet,
                                 "submitter": submitter},
                                proxy,
                                debug = args.debug,
                                client_type = client_type)
                # print(resp)

                # FLU-API-CHANGES: The FLU-API returns three attributes in it's respose:
                # isolate_ids: a dict with the isolate-id created while submitting to the name of the submission
                # segment_ids: same for segments
                # messages: all messages from the call (a list of dicts)
                for virus_name, accession_id in resp.get("isolate_ids", {}).items():
                    log("epi_isl_id", "%s; %s" % (virus_name, accession_id))

                for virus_name, segment_id in resp.get("segment_ids", {}).items():
                    log("epi_id", "%s; %s" % (virus_name, segment_id))
                # print(resp)
                for response_ in resp.get("messages", []):
                    # print(response_, type(response_))
                    log("msg", response_.get("msg"))
                    message_count += 1

            # close session
            resp = call_api({"cmd": "state/session/logoff",
                             "api": {"version": 1},
                             "sid": sid},
                            proxy,
                            debug = args.debug,
                            client_type = client_type)


        return 0

    elif args.subparser_name == "labs":
        "'labs' is an alpha feature"
        # get the auth-token from the file or from the command line
        # print('entered labs')
        from pathlib import PurePath, Path
        if not Path(args.token).exists():
            sys.exit(f"{args.token} does not exist.  Create file using 'epiflu_cli authenticate'.")

        auth_token = load_authentication_token("flu", args.token, True)
        client_id = auth_token['client-id']
        auth_token = auth_token['token']

        if client_id.startswith("TEST-"):
            client_type = "test"
        elif client_id.startswith("LOCAL-"):
            client_type = "local"

        cmd = "data/flu/get_labs"
        resp = call_api({"cmd": "state/session/logon", #cmd is logon
                         "api": {"version": 1},
                         "ctx": "flu",
                         "client_id": client_id,
                         "auth_token": auth_token},
                        proxy,
                        debug=args.debug,
                        client_type=client_type)

        time.sleep(0.5) # give system time to save session

        if resp["rc"] == "auth_token_invalid":
            log(args.log, "invalid_token", "invalid auth-token")
            return 1
        elif resp["rc"] != "ok":
            log(args.log, "error", "unexpected response from GPS-API", repr(resp))
            return 1

        sid = resp["sid"]


        resp = call_api({"cmd": cmd,
                         "api": {"version": 1},
                         "sid": sid,
                         "ctx": "flu"},
                        proxy,
                        debug = args.debug,
                        client_type = client_type)
        # print(resp)
        if resp["rc"] == "ok":
            for lab_id, lab in resp["labs"]:
##                log(args.log, "lab", f"{lab_id}; {lab}")
                print(lab_id, ":", lab)


        # close session
        resp = call_api({"cmd": "state/session/logoff",
                         "api": {"version": 1},
                         "ctx": "flu",
                         "sid": sid},
                        proxy,
                        debug = args.debug,
                        client_type = client_type)

        return 0
