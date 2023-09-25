import sys
import requests
from bs4 import BeautifulSoup
import csv

page_target = "Tevetron"
page_category = "IC"

componentsDict = {
    "Product Number" : "",
    "Product Package" : "",
    "Product Price" : "",
    "Product Availability" : "",
}

if (page_target == "Tevetron"):
    f = open('./database/tevetron.csv', 'w', encoding='UTF8', newline='')
elif (page_target == "Elmatis"):
    f = open('./database/elmatis.csv', 'w', encoding='UTF8', newline='')
else:
    print("ERROR: Target website is not defined or invalid!")
    sys.exit(1)

writer = csv.writer(f)

if (page_target == "Tevetron"):
    if (page_category == "IC"):
        URL_base = "https://www.tevetron.hr/hr/webshop/ic/16/"
    elif (page_category == "transistors"):
        URL_base = "https://www.tevetron.hr/hr/webshop/tranzistori/68/"
    else:
        print("ERROR: Tevetron doesn't have the requested category!")
        sys.exit(2)
elif (page_target == "Elmatis"):
    URL_base = "http://www.elmatis.hr/Articles.aspx"
    if (page_category == "IC"):
        elmatis_category = "I. C. KRUGOVI I PODNOŽJA"
    elif (page_category == "transistors"):
        elmatis_category = "TRANZISTORI, LISKUNI, MODULI"
    else:
        print("ERROR: Elmatis doesn't have the requested category!")
        sys.exit(3)

page = requests.get(URL_base)
soup = BeautifulSoup(page.content, "html.parser")

if (page_target == "Tevetron"):
    results = soup.find_all("div", class_="product-inner")
    i = 0
    while results:
        for result in results:
            productNumber = result.find("h3").text.strip()
            productPrice = result.find("span", class_ = "cprice1").text.strip()
            productPackage = result.find("h4").text.strip()
            productAvailability = result.find("span", class_="raspolozivost_2 da").text.strip() if result.find("span", class_="raspolozivost_2 da") != None else result.find("span", class_="raspolozivost_2 ne").text.strip()
            writer.writerow([productNumber, productPrice, productPackage, productAvailability])
        i += 1
        if (i%10 == 0):
            print(f"Status: {i}.")
        URL = URL_base + str(i)
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")
        results = soup.find_all("div", class_="product-inner")
elif (page_target == "Elmatis"):
    ## find all links for a given category subpages
    category_list = soup.find("div", id="navigationContainer").find_all("a")
    category_links = []
    N = len(category_list)
    found_subpage = False
    for i_cat in range(N):
        subpage_addr = category_list[i_cat].get("href")
        if (subpage_addr == "#"):
            if (found_subpage):
                break
            subpage_name = category_list[i_cat].text.strip()
            if (subpage_name == elmatis_category):
                found_subpage = True
        elif (found_subpage):
            category_links.append(subpage_addr)
    if (len(category_links) == 0):
        print("No such category")
        sys.exit(4)
    ## go to every subpage for a given category
    URL_base_2 = "http://www.elmatis.hr"
    for subpage_link in category_links:
        URL_subpage = URL_base_2 + subpage_link
        elmatis_subpage = requests.get(URL_subpage)
        req_page = 1
        while True:
            elmatis_soup = BeautifulSoup(elmatis_subpage.content, "html.parser")
            if(elmatis_subpage.status_code != 200):
                if (elmatis_soup.find("title").get_text() == "Specified cast is not valid."):
                    elmatis_subpage = requests.get(URL_subpage)
                    continue
                else:
                    break
            VIEWSTATEvalue  = elmatis_soup.find("input", id="__VIEWSTATE").get("value")
            VIEWSTATEGENERATORvalue  = elmatis_soup.find("input", id="__VIEWSTATEGENERATOR").get("value")
            EVENTVALIDATIONvalue  = elmatis_soup.find("input", id="__EVENTVALIDATION").get("value")
            results = elmatis_soup.find("table", class_="list")
            rows = results.find_all("tr")
            Nrows = len(rows)
            ## last two rows are for page numbers
            for i in range(Nrows-2):
                row = rows[i]
                cells = row.find_all("td")
                if (len(cells) > 0):
                    productNumber = cells[0].text.strip()
                    productDesc = cells[1].text.strip()
                    productPrice = cells[2].find("div", class_="price-kn").text.strip()
                    productAvailability = cells[3].text.strip()
                    writer.writerow([productNumber, productPrice, productDesc, productAvailability])
            req_page += 1
            data = {
                "__EVENTTARGET" : "ctl00$Main$ucProductList$grdProductListPublic",
                "__EVENTARGUMENT" : "Page${}".format(req_page),
                "__VIEWSTATEGENERATOR" : VIEWSTATEGENERATORvalue,
                "__VIEWSTATE" : VIEWSTATEvalue,
                "__EVENTVALIDATION" : EVENTVALIDATIONvalue
            }
            elmatis_subpage = requests.post(URL_subpage, data)

f.close()