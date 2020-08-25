# GET NEW PUPPIE!
# the loop runs every 5 minutes
# each time it runs a request for all interesting breeds and gets a response
# if it's the first run it just adds to the list
# if it's not the first run it also compares the current list with the new list
# if there is a new puppy in the new list sends a notification email to specified account

import subprocess
import time
import smtplib, ssl
import json
import configparser

shelter_breeds = [
    "AUST%20CATTLE%20DOG",
    "AUST%20SHEPPERD",
    "BELG%20MALINOIS",
    "BELG%20SHEEPDOG",
    "BORDER%20COLLIE",
    "COLLIE%20SMOOTH",
    "DUTCH%20SHEPHERD",
    "ENG%20SHEPHERD",
    "FLAT%20COAT%20RETR",
    "FOX%20TERR%20SMOOTH",
    "GOLDEN%20RETR",
    "JACK%20RUSS%20TERR",
    "LABRADOR%20RETR",
    "SHETLD%20SHEEPDOG"
]

petfinder_breeds = [
    "breed\[\]=Australian%20Cattle%20Dog%20%2F%20Blue%20Heeler",
    "breed\[\]=Australian%20Shepherd",
    "breed\[\]=Belgian%20Shepherd%20%2F%20Malinois",
    "breed\[\]=Belgian%20Shepherd%20%2F%20Sheepdog",
    "breed\[\]=Black%20Labrador%20Retriever",
    "breed\[\]=Border%20Collie&",
    "breed\[\]=Cattle%20Dog",
    "breed\[\]=Chocolate%20Labrador%20Retriever",
    "breed\[\]=Dutch%20Shepherd",
    "breed\[\]=English%20Shepherd",
    "breed\[\]=Flat-Coated%20Retriever",
    "breed\[\]=Golden%20Retriever",
    "breed\[\]=Jack%20Russell%20Terrier",
    "breed\[\]=Labrador%20Retriever",
    "breed\[\]=Retriever",
    "breed\[\]=Sheep%20Dog",
    "breed\[\]=Shepherd",
    "breed\[\]=Shetland%20Sheepdog%20%2F%20Sheltie",
    "breed\[\]=Smooth%20Collie",
    "breed\[\]=Smooth%20Fox%20Terrier",
    "breed\[\]=Yellow%20Labrador%20Retriever"
]

petfinder_breeds_url = "&".join(petfinder_breeds)

ssl_port = 465
smtp_server = "smtp.gmail.com"

shelter_message = """\
Subject: new doggie found with id <id>
"""

config = configparser.ConfigParser()
config.read("doggie.ini")
sender_email = config["DEFAULT"]["sender_email"]
sender_password = config["DEFAULT"]["sender_password"]
receiver_email = config["DEFAULT"]["receiver_email"].split(",")

def get_doggies():
    current_ids = []
    # la county shelter
    for breed in shelter_breeds:
        list_of_doggies = subprocess.run(
            ["curl", "https://api.lacounty.gov/accsearch/AnimalSearchServlet?callback=animal&pageNumber=1&pageSize=12&animalCareCenter=ALL&animalType=DOG&sex=ALL&breed=" + breed + "&animalAge=LT1Y&animalSize=ALL&animalID=&test=9"],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            universal_newlines=True)

        clean_output = list_of_doggies.stdout.replace("animal(", "").replace(")", "")
        try: 
            doggies = json.loads(clean_output)
            print("list of doggies for breed " + breed, doggies["animals"])
            for dog in doggies["animals"]:
                current_ids.append(dog["ANIMAL_ID"])
        except Exception as e:
            print("an error occured:", e, clean_output)
    
    # petfinder
    petfinder_doggies = subprocess.run(
        ["curl", "https://www.petfinder.com/search/?page=1&limit\[\]=40&status=adoptable&token=HGsFL0jv1vRbYEXuY06hbrddekWMEWqOTf9AdPiwVjQ&days_on_petfinder[]=1&distance\[\]=100&type\[\]=dogs&sort\[\]=nearest&age\[\]=Baby&" 
        + petfinder_breeds_url 
        + "&location_slug\[\]=us%2Fca%2F91301&include_transportable=0", 
        "-H", 
        "X-Requested-With: XMLHttpRequest"],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        universal_newlines=True)
    
    clean_petfinder_output = petfinder_doggies.stdout
    
    try: 
        petfinder_doggies = json.loads(clean_petfinder_output)
        for dog in petfinder_doggies["result"]["animals"]:
            current_ids.append(dog["animal"]["name"])
    except Exception as e:
        print("an error occured:", e)

    return current_ids

subprocess.run(["tput", "bel"])        

initial_ids = get_doggies()
print("initial ids ", initial_ids)

while True:
    print("========= New request =============")
    current_ids = get_doggies()
    print("current ids ", current_ids)

    difference = list(set(current_ids) - set(initial_ids))
    
    initial_ids = initial_ids + difference
    print("New ids are ", difference)

    for new_id in difference:
        print("sending email for ", new_id)
        with smtplib.SMTP_SSL(smtp_server, ssl_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, shelter_message.replace("<id>", new_id))
        subprocess.run(["tput", "bel"])

    print("going to sleep, Zzzz")    
    time.sleep(300)
