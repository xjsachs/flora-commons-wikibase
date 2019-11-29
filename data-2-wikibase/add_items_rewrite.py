import wikidataintegrator as WI
import requests, csv, sys, re

"""
    NOTES:
    The wikidataintegrator module was built to do a sepcific task, to populate 
    wikdiata with Genes, Proteins, Diseases, Drugs and other domain specific stuff
    so we need to overwrite a few pieces of it in order to make it work for our domain spcific stuff
    and also work on our own installation of wikibase not wikidata
"""

# overwrite the property store that comes built in with wikidataintergrator
# these are unique values that should be unique in our data
# if you have spefifc properties that should be unique across your data you can add them here
# it is useful because then you can use that property to pull up the item without knowing its QID number
WI.wdi_core.WDItemEngine.core_props = {
    # https://github.com/SuLab/WikidataIntegrator/blob/master/wikidataintegrator/wdi_property_store.py
    'P6': {
        'datatype': 'string',
        'name': 'LJ Slug ID',
        'domain': ['linkedjazz'],  # this is a wikidataintergrator thing, to group properties together
        'core_id': True
    }
}

# use this specific property for this run of the script
use_unique_property = 'P6:string'
# Change the pwd paramater here 
bot_user = 'WikibaseAdmin'
bot_pwd = 'bot@r2qa459dq7t7l9j254bkl39ji62tqk4r'

if __name__ == "__main__":

    # if len(sys.argv) == 1:
    #   raise ValueError('Missing input CSV file')

    csv_path = 'add_core_items.csv'
    csv_file = open(csv_path, 'r')
    csv_reader = csv.DictReader(csv_file)

    login_instance = WI.wdi_login.WDLogin(user=bot_user, pwd=bot_pwd,
                                          mediawiki_api_url="http://localhost:8181/w/api.php")

    # we are going to just create the entities and any P values provided in the CSV
    complete_data = []
    errors_data = []

    for row in csv_reader:
        row = dict(row)

        data = []

        # properties stuff     
        for key in row:

            # is it a property field
            if key.find(':') > -1 and key[0] == "P":
                PID, data_type = key.split(':')

                # there are few other data types need to add...
                try:
                    if data_type.lower() == 'string':
                        if row[key] is not None and row[key].strip() != '':
                            statement = WI.wdi_core.WDString(value=row[key], prop_nr=PID)
                            data.append(statement)
                    elif data_type.lower() == 'url':
                        if row[key] is not None and row[key].strip() != '':
                            statement = WI.wdi_core.WDUrl(value=row[key], prop_nr=PID)
                            data.append(statement)
                    elif data_type.lower() == 'wikibase-item':
                        if row[key] is not None and row[key].strip() != '':
                            statement = WI.wdi_core.WDItemID(value=row[key], prop_nr=PID)
                            data.append(statement)


                except Exception as e:
                    print("There was an error with this one, skipping:")
                    print(row)
                    print(e)
                    errors_data.append(row)
                    data = "error"

        if data == 'error':
            continue

        # change this to whatever field you are using to be unique across the data
        # item_name = None if row['Label'] is None or row['Label'].strip() == '' else row['Label']
        # here im using this P35 property, a legacy identifier that will be unique across the dataset
        if use_unique_property in row:
            item_name = row[use_unique_property]
        else:
            item_name = None

        # what domain is this data going into, can be None
        domain = 'linkedjazz'

        try:
            # instead of item_name you can use "item_id" and pass the QID if you have that
            wd_item = WI.wdi_core.WDItemEngine(new_item=True, data=data,
                                               mediawiki_api_url="http://localhost:8181/w/api.php")

            # set the label and description if exists
            if 'Label' in row:
                if row['Label'] is not None and row['Label'].strip() != '':
                    wd_item.set_label(row['Label'])
                    print("I did this!!")

            if 'Description' in row:
                if row['Description'] is not None and row['Description'].strip() != '':
                    wd_item.set_description(row['Description'])

            # can update instead and tell it which properties to append to not overwrite
            # wd_item.update(data,append_value=['P17'])

            # write
            r = wd_item.write(login_instance)
            print("goodbye!")

            # QID is returned
            row['QID'] = r

            print(row['QID'], row['Label'])

            complete_data.append(row)


        except Exception as e:
            print("There was an error with this one, skipping - I AM HERE:")
            print(row)
            print(e)
            errors_data.append(row)
            data = "error"

    csv_file.close()

    with open(csv_path + '_updated.csv', 'w') as out:

        fieldnames = list(complete_data[0].keys())
        writer = csv.DictWriter(out, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(complete_data)

    if len(errors_data) > 0:
        with open(csv_path + '_errors.csv', 'w') as out:
            fieldnames = list(errors_data[0].keys())
            writer = csv.DictWriter(out, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(errors_data)
