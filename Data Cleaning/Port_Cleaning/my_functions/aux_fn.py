#Libraries
import pandas as pd
import numpy as np
import re
import traceback
from fuzzywuzzy import process
#------------------------
#1 Extract combined DataFrame
path_1 = 'Data/MyPoert AUG sheet1.xlsx'
def extract_original_df(path_1=path_1):
    try:
        countries_name = pd.ExcelFile(path_1).sheet_names
        original_df = pd.DataFrame(columns=['Trip','Way_Price','Country'])

        for country in countries_name:
            #Read File
            temp_df = pd.read_excel(path_1,sheet_name=country).iloc[:,:2]
            temp_df.columns = ['Trip','Way_Price']
            #Check On Trip/Price Column for data loaded on multiple rows
            check = (temp_df['Trip'].isna())&(temp_df['Way_Price'].notna())
            check_df = temp_df[check]
            if sum(check_df.index) > 0 : 
                for idx in check_df.index:
                    #Concat rows info
                    temp_df['Way_Price'].iloc[idx-1] = temp_df['Way_Price'].iloc[idx-1] + ' ' +temp_df['Way_Price'].iloc[idx]
            temp_df = temp_df.dropna()
            temp_df = temp_df.apply(lambda x : x.str.lower().str.replace('r\s+',' ',regex=True))
            temp_df['Country'] = country.lower()
            original_df = pd.concat([original_df,temp_df],ignore_index=True,axis=0)
        original_df['Way_Price'] = original_df['Way_Price'].str.replace('\n',' ')
        for col in original_df.columns:
            original_df[col] = original_df[col].apply(lambda x: re.sub(r'\s+',' ',x).strip())
    except Exception as e:
        print('Error Occur extract_original_df function \n')
        print(traceback.format_exc())
    else:
        return original_df
#-----------------------------------------
#2 Extract info from original_df

def extract_from_to_price(df):
    temp_df = df.copy()
    try:
        #Trip extracting
        from_to_list = temp_df['Trip'].apply(lambda x: re.findall(r'from(.*?)to(.*?)$', x)[0]).values
        temp_df['Trip_From'], temp_df['Trip_To'] = zip(*[(trip_from.strip(),trip_to.strip()) for trip_from,trip_to in from_to_list])
        
        #Way_Price Extracting
        def way(x):
            if 'one' in x:
                return 'o'
            elif 'round' in x:
                return 'r'
            else:
                return 'unknown'

        #Extract way
        temp_df['Way'] = temp_df['Way_Price'].apply(way)
        #Extract price
        temp_df['Price'] = temp_df['Way_Price'].apply(lambda x: re.findall(r'\d+',x)[0])
    
    except Exception as e:
        print('Error Occur extract_from_to_price function \n')
        print(traceback.format_exc())
    else:
        temp_df.drop(columns=['Way_Price','Trip'],inplace=True)
        return temp_df.reset_index(drop=True)
#--------------------------------------
#3 Import ports cities id's & codes 

path_2 = 'Data/Ports_ceties_codes_and_IDs.xlsx'
def extract_id_code(path_2=path_2):
    temp_df = pd.read_excel(path_2)
    temp_df[['City','Port Name','Code']] = temp_df.iloc[:,:-1].apply(lambda x : x.str.lower())
    temp_df.columns = [col.replace(' ','_') for col in temp_df.columns]
    return temp_df

#--------------------------------------
#4 Handling some ports errors

def handling_port_errors(original_df,city_ports_df):
    """Handling Some Data Entry Errors In Port Names"""
    original_copy = original_df.copy()
    city_ports_copy = city_ports_df.copy()
    columns = ['Trip_From','Trip_To']
    error_ports = []
    report_ports_names = []
    correct_ports = city_ports_copy['Port_Name'].values
    check_ports = set(np.append(original_copy['Trip_From'].unique(),original_copy['Trip_To'].unique()))
    for port in check_ports:
        #Find the closest match to the misspelled city
        match, score = process.extractOne(port, correct_ports)
        #Check if high score --> import correct port name
        if score >= 80 :
            original_copy[columns] = original_copy[columns].replace(f'{port}',f'{match}')
        #If score < 75 --> add value to check it later
        else:
            error_ports.append(port)
    #Check maybe city entered instade of port OR new port to our dataset
    if len(error_ports)==0:
        #No ports name error
        return original_copy.reset_index(drop=True),report_ports_names
    else:
        cities_list = city_ports_copy['City'].values
        for val in error_ports:
            match, score = process.extractOne(val,cities_list)
            if score >= 95: #Confident about city replaced with port 
                temp_df = city_ports_copy[city_ports_copy['City']==match]
                if len(temp_df)==1: #1 city --> 1 port
                    port_to_replace = temp_df['Port_Name'].values[0]
                    original_copy[columns] = original_copy[columns].replace(f'{val}',f'{port_to_replace}')
                elif len(temp_df)>1: #City with multiple ports (Must Report)
                    idxs = original_copy[(original_copy['Trip_From']==f'{val}')|(original_copy['Trip_To']==f'{val}')].index.to_list()
                    report_ports_names.append((val,idxs))
                    original_copy.drop(index=idxs,inplace=True)
                else: #Port not found in cities
                    pass
            else: #Report if port not in database (Maybe new port)
                idxs = original_copy[(original_copy['Trip_From']==f'{val}')|(original_copy['Trip_To']==f'{val}')].index.to_list()
                report_ports_names.append((val,idxs))
                original_copy.drop(index=idxs,inplace=True)
        return original_copy.reset_index(drop=True),report_ports_names
#-------------------------------------------------------
#5 modifing some issues in original_df,city_ports_df

def mod_orig_city_dfs(original_df,city_ports_df):
    orig_copy = original_df.copy()
    city_port_copy = city_ports_df.copy()
    obj_orig_cols = orig_copy.select_dtypes('object').columns
    orig_copy[obj_orig_cols] = orig_copy[obj_orig_cols].apply(lambda x : x.str.strip())
    orig_copy['Price'] = orig_copy['Price'].astype(int)
    city_orig_cols = city_port_copy.select_dtypes('object').columns
    city_port_copy[city_orig_cols] = city_port_copy[city_orig_cols].apply(lambda x : x.str.strip())
    return orig_copy,city_port_copy
#-------------------------------------------------------
#6 Offer Template

def offers_template(original_df,city_ports_df):
    try:
        path_3 = 'Data/Countries IDs.xlsx'
        countries_ids = pd.read_excel(path_3)
        countries_ids['Country'] = countries_ids['Country'].apply(lambda x : x.lower().strip())

        offer_temp = {'port_from_id':[],'port_to_id':[],'trip_type':[],'url':[],'publish_date':[],'expire_date':[]}
        offer_cont = {'offer_url':[],'country_id':[],'price':[]}
        def en_to_ar_num(number):
            ar_dict = {'0':'۰','1':'١','2':'٢','3':'۳','4':'٤','5':'٥','6':'٦','7':'۷','8':'۸','9':'۹'}
            return "".join([ar_dict[char] for char in str(number)])

        orig_copy = original_df.copy()
        city_copy = city_ports_df.copy()
        #Importing
        offer_temp['trip_type'] = list(orig_copy['Way'].values)
        for _,row in orig_copy.iterrows():
            offer_temp['port_from_id'].append(city_copy[city_copy['Port_Name']==row['Trip_From']]['ID'].values[0])
            offer_temp['port_to_id'].append(city_copy[city_copy['Port_Name']==row['Trip_To']]['ID'].values[0])
            url = f"{city_copy[city_copy['Port_Name']==row['Trip_From']]['Code'].values[0]}-{city_copy[city_copy['Port_Name']==row['Trip_To']]['Code'].values[0]}-{row['Way']}"
            offer_temp['url'].append(url)
            #-------------
            offer_cont['offer_url'].append(url)
            offer_cont['country_id'].append(countries_ids[countries_ids['Country']==row['Country']]['ID'].values[0])
            #price
            ar_price = en_to_ar_num(row['Price'])
            offer_cont['price'].append(dict(en=row['Price'],ar=ar_price,gr=row['Price'],it=row['Price'],cz=row['Price'],fr=row['Price'],sk=row['Price']))

        offer_temp['publish_date'] = list(np.repeat('2024-04-04',len(orig_copy)))
        offer_temp['expire_date'] = list(np.repeat('2024-05-07',len(orig_copy)))

        offer_temp_df = pd.DataFrame(offer_temp)
        offer_temp_df.drop_duplicates(inplace=True,ignore_index=True)
        offer_cont_df = pd.DataFrame(offer_cont)
    except Exception as e:
        print(f'Error Importing {e}')
    else:
        offer_temp_df.to_excel('offer_template.xlsx',index=False),offer_cont_df.to_excel('offer_content.xlsx',index=False)
        print('Done Importing!')