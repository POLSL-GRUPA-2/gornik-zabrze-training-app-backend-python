import sys
import random
import time
import string

if len(sys.argv) != 3:
    print("Two arguments needed: table name and number of entries")
    exit()

random.seed(time.time())
if sys.argv[1] == "users":
    names_file = open("names.txt","r+") 
    lastnames_file = open("lastnames.txt","r+")

    names = names_file.read().splitlines()
    lastnames = lastnames_file.read().splitlines()



    for s in range(int(sys.argv[2])):
        
        name = names[random.randrange(len(names))]
        lastname = lastnames[random.randrange(len(lastnames))]
        email = name[0:4].lower() + lastname[0:3].lower() + str(random.randrange(9)) + str(random.randrange(9)) + str(random.randrange(9)) + "@studnet.polsl.pl"
        password = ''.join(random.sample(string.ascii_lowercase, 12))

        query = "insert into {0} (first_name, last_name, email, password_hash) values ('{1}', '{2}', '{3}', '{4}');".format(sys.argv[1], name, lastname, email, password)

        print(query)
else:
    print ("Invalid table name")
