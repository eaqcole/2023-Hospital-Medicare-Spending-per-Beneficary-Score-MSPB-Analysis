''' Medicare Spending Per Beneficiary Analyzer
Date: October 5, 2025
Name: Emily Quick-Cole

Background: Medicare is a federal health insurance program in the United States primarily for people age 65 or older,
but also for younger individuals with certain disabilities, End-Stage Renal Disease (permanent kidney failure),
or Amyotrophic Lateral Sclerosis (ALS). It provides health care coverage through its different parts, such as Part A
for hospital stays and hospice care, Part B for doctors' services and outpatient care, Part C (Medicare Advantage)
which offers a bundled private plan option, and Part D for prescription drug coverage.

According to the Centers for Medicaid and Medicare Services (CMS), The Medicare Spending Per Beneficiary (MSPB)
Measure shows whether Medicare spends more, less, or about the same for an episode of care (episode) at a specific
hospital compared to all hospitals nationally. An MSPB episode includes Medicare Part A and Part B payments for
services provided by hospitals and other healthcare providers the 3 days prior to, during, and 30 days following a
patient's inpatient stay. This measure evaluates hospitals' costs compared to the costs of the national median
(or midpoint) hospital. This measure takes into account important factors like patient age and health status
(risk adjustment) and geographic payment differences (payment-standardization).

Purpose: To produce an informational one to two-page report on states' median MSPB scores using CMS data from 2023.

Data Source: https://data.cms.gov/provider-data/dataset/rrqw-56er

Date of Data Download: October 2, 2025

Results: See PDF output.
'''

# Import relevant packages needed for data exploration and analysis
import numpy as np
import matplotlib.colors as mcolors
import geopandas as gpd #pip install geopandas
from shapely.geometry import Polygon
import os
from fpdf import FPDF
import time
import pandas as pd
import matplotlib.pyplot as plt
import dataframe_image as dfi #pip install dataframe_image


''' Initial Data Cleaning '''
# Set working directory, change this to match relevant path
new_directory_path = "/Users/emilyquick-cole/Documents/Python/medicare_analysis"
os.chdir(new_directory_path)

#Load your dataset (e.g., CSV file)
df = pd.read_csv('Medicare_Hospital_Spending_Per_Patient-Hospital.csv')

#Save as a dataframe
df = pd.DataFrame(df)

#Count the number of rows within the dataset--this is the number of hospitals
total_hospitals = len(df)
print(f"There are {total_hospitals} hospitals in this dataset.")

# Count the number of rows missing a Score value
rows_with_missing_data = df['Score'].isnull().sum() #No rows are missing data; however, some rows have N/A indicated
print(f"Number of rows with missing data: {rows_with_missing_data}")

# Count rows where the Score column is indicated as "Not Available"
na_count = (df['Score'] == 'Not Available').sum()
print(f"{na_count} hospitals reported that scores were not available") #1,682 rows are indicated as Not Available

#Save not available scores to a new data frame and drop them from original dataframe
na_df = df[df['Score'] == 'Not Available']
print('na_df score col', na_df['Score'])

#Remove rows that contain a Score value of 'Not Available'
score_df = df[df['Score'] != 'Not Available']

#Check that the only values remaining can be converted to a float
print('Unique values of score are', df['Score'].unique())

#set Score variable to a float
score_df['Score'] = score_df['Score'].astype('float64')

#Set the State column to a string
score_df['State'] = score_df['State'].astype('string')

'''Formatting Data for Map Visual '''
#Group hospitals by state and take their median Score and reset the index of the resulting dataframe
med_df = score_df.groupby(['State'])['Score'].median().reset_index()

#sort the data from greatest to least
med_df = med_df.sort_values(by=['Score'], ascending=False)
print(f"The median Medicare Spending per Beneficiary Score (MSPB) by state is {med_df}.")

#print the number of states with a score of 1.0, above 1.0, and below 1.0
above1 = len(med_df[med_df['Score'] > 1.0])
at1 = len(med_df[med_df['Score'] == 1.0])
below1 = len(med_df[med_df['Score'] < 1.0])
print(f"{above1} states have a median score over 1.0. {at1} states have a median score of 1.0. {below1} states have a median score less than 1.0.")


'''Map Visual: Take the median MSPB Score of all States and plot them on a map of the U.S. color coding based on score'''
#Read in the datafile with U.S. map shape data
gdf = gpd.read_file('/Users/emilyquick-cole/Documents/Python/medicare_analysis/cb_2018_us_state_500k')

#Merge the Geopandas Dataframe with MSPB data based on 'State'
gdf = gdf.merge(med_df,left_on='STUSPS',right_on='State')

#Check that the dataframes merged correctly
gdf.to_excel('/Users/emilyquick-cole/Documents/Python/medicare_analysis/gdf.xlsx', index=False)

#We can re-project coordinates for any of the components of our map using the geopandas command .to_crs()
gdf.to_crs({'init':'epsg:2163'})

#Create new boxes to map them in underneath and to the left of the continental US.
#Create a "copy" of gdf for re-projecting
visframe = gdf.to_crs({'init':'epsg:2163'})

#Create figure and axes for with Matplotlib for main map
fig, ax = plt.subplots(1, figsize=(18, 14))

#Remove the axis box from the main map
ax.axis('off')

#Create map of all states except AK and HI in the main map axis
visframe[~visframe.STUSPS.isin(['HI','AK'])].plot(color='lightblue', linewidth=0.8, ax=ax, edgecolor='0.8')

#Add Alaska Axis (x, y, width, height)
akax = fig.add_axes([0.1, 0.17, 0.17, 0.16])

#Add Hawaii Axis(x, y, width, height)
hiax = fig.add_axes([.28, 0.20, 0.1, 0.1])

#We'll later map Alaska in "akax" and Hawaii in "hiax"

#Apply this to the gdf to ensure all states are assigned colors by the same func
def makeColorColumn(gdf,variable,vmin,vmax):
    # apply a function to a column to create a new column of assigned colors & return full frame
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
    mapper = plt.cm.ScalarMappable(norm=norm, cmap=plt.cm.YlOrBr)
    gdf['value_determined_color'] = gdf[variable].apply(lambda x: mcolors.to_hex(mapper.to_rgba(x)))
    return gdf

#S the value column that will be visualised
variable = 'Score'

#Make a column for value_determined_color in gdf
#Set the range for the choropleth values with the upper bound the rounded up maximum value
vmin, vmax = gdf.Score.min(), gdf.Score.max() #math.ceil(gdf.pct_food_insecure.max())

#Choose the continuous colorscale "YlOrBr" from https://matplotlib.org/stable/tutorials/colors/colormaps.html
colormap = "YlOrBr" #yellow brown color scale
gdf = makeColorColumn(gdf,variable,vmin,vmax)

#Create "visframe" as a re-projected gdf using EPSG 2163 for CONUS
visframe = gdf.to_crs({'init':'epsg:2163'})

#Create figure and axes for Matplotlib
fig, ax = plt.subplots(1, figsize=(18, 14))

#Remove the axis box around the vis
ax.axis('off')

#Set the font for the visualization to Helvetica
hfont = {'fontname':'Helvetica'}

#Use this to add a title and annotation
ax.set_title('Figure 1: 2023 Median State MSPB Scores', **hfont, fontdict={'fontsize': '38'}) #, 'fontweight' : 'bold'

#Create colorbar legend
fig = ax.get_figure()

#Add colorbar axes to the figure
#This will take some iterating to get it where you want it [l,b,w,h] right
#l:left, b:bottom, w:width, h:height; in normalized unit (0-1)
cbax = fig.add_axes([0.89, 0.21, 0.03, 0.31])

cbax.set_title("Median Medicare Spending\nper Beneficiary Score", **hfont, fontdict={'fontsize': '15', 'fontweight' : '0'})

#Add color scale
sm = plt.cm.ScalarMappable(cmap=colormap,norm=plt.Normalize(vmin = vmin, vmax=vmax))

#Reformat tick labels on legend
sm._A = []
fig.colorbar(sm, cax=cbax) #, format=comma_fmt
tick_font_size = 16
cbax.tick_params(labelsize=tick_font_size)

# annotate the data source, date of access, and hyperlink
ax.annotate("Data: CMS Medicare Spending Per Beneficiary - Hospital, accessed 2 Oct 2025\nhttps://data.cms.gov/provider-data/dataset/rrqw-56er#data-table",
            xy=(0.22, .085), xycoords='figure fraction', fontsize= 14, color='#555555')

# create map
# Note: we're going state by state here because of unusual coloring behavior when trying to plot the entire dataframe using the "value_determined_color" column
for row in visframe.itertuples():
    if row.State not in ['AK','HI']:
        vf = visframe[visframe.State==row.State]
        c = gdf[gdf.State==row.State][0:1].value_determined_color.item()
        vf.plot(color=c, linewidth=0.8, ax=ax, edgecolor='0.8')

#Add Alaska
akax = fig.add_axes([0.1, 0.17, 0.2, 0.19])
akax.axis('off')
#Polygon to clip western islands
polygon = Polygon([(-170,50),(-170,72),(-140, 72),(-140,50)])
alaska_gdf = gdf[gdf.State=='AK']
alaska_gdf.clip(polygon).plot(color=gdf[gdf.State=='AK'].value_determined_color, linewidth=0.8,ax=akax, edgecolor='0.8')

#Add Hawaii
hiax = fig.add_axes([.28, 0.20, 0.1, 0.1])
hiax.axis('off')

#Polygon to clip western islands
hipolygon = Polygon([(-160,0),(-160,90),(-120,90),(-120,0)])
hawaii_gdf = gdf[gdf.State=='HI']
hawaii_gdf.clip(hipolygon).plot(column=variable, color=hawaii_gdf['value_determined_color'], linewidth=0.8,ax=hiax, edgecolor='0.8')

# bbox_inches="tight" keeps the vis from getting cut off at the edges in the saved png
# dip is "dots per inch" and controls image quality.  Many scientific journals have specifications for this
# https://stackoverflow.com/questions/16183462/saving-images-in-python-at-a-very-high-quality
fig.savefig(os.getcwd()+'/MSPBmap.png',dpi=400, bbox_inches="tight")


'''Regional Table: generate a table grouping states by region, finding median MSPB score and total hospitals from which
median is based on'''
#Create the regional categories
ne = ['ME', 'VT', 'NH', 'CT','MA', 'RI']
midatl = ['NY', 'PA', 'NJ', 'MD', 'DE', 'DC']
midwest = ['OH', 'MI', 'IN', 'IL', 'WI', 'IA', 'MO', 'MN', 'ND', 'SD', 'NE', 'KS']
southwest = ['OK', 'TX', 'AZ', 'NM']
west = ['CO', 'WY', 'MT', 'UT', 'ID', 'WA', 'OR', 'NV', 'CA', 'AK', 'HI']
south = ['VA', 'WV', 'KY', 'NC', 'TN', 'AR', 'SC', 'GA', 'AL', 'MS', 'LA', 'FL']

#Create new Region column
score_df.insert(loc = 6, column = 'Region', value = np.nan)

#Iterate through the data and assign a region to each row based on the state a hospital is located in
score_df = score_df.reset_index()  # make sure indexes pair with number of rows

#Create a function to
def categorize_region(value):
    if value in ne:
        return 'North East'
    elif value in midatl:
        return 'Mid-Atlantic'
    elif value in midwest:
        return 'Midwest'
    elif value in southwest:
        return 'South West'
    elif value in west:
        return 'West'
    elif value in south:
        return 'South'

#Apply the function to assign Region categories
score_df['Region'] = score_df['State'].apply(categorize_region)

# Export to an Excel document to review the data
score_df.to_excel('/Users/emilyquick-cole/Documents/Python/medicare_analysis/score_df.xlsx', index=False)

'''Formatting Data for Regional Table: group hospitals by state and take their median Score and reset the index of 
the resulting dataframe'''

#Set the region as a categorical variable
score_df['Region'] = score_df['Region'].astype('category')

#take median of score by region
regional_df = score_df.groupby(['Region'])['Score'].median().reset_index(drop= False)

#Count the number of hospitals with recorded scores for each region
reg_hosp_df = score_df['Region'].value_counts()

#Count the number of hospitals with no recorded scores ("not available") for each region
na_df['Region'] = na_df['State'].apply(categorize_region)
print("na_df is", na_df)

# Export to an Excel document to review the data
na_df.to_excel('/Users/emilyquick-cole/Documents/Python/medicare_analysis/na_df.xlsx', index=False)
na_hosp_df = na_df['Region'].value_counts()
print("na_hosp_df is", na_hosp_df)

#Merge the dataframes on Region
#First merge the dataframe with median Score values and hospitals that reported
table_df = regional_df.merge(reg_hosp_df,left_on='Region',right_on='Region')

#Then merge that dataframe with the counts of hospitals that had "Not Available" reported
table_df = table_df.merge(na_hosp_df,left_on='Region',right_on='Region')

#Create a new column that totals the number of hospitals with reported scores and hospitals with "not available" scores
table_df['Total Hospitals'] = table_df['count_x'] + table_df['count_y']

#Reorganize the table so that the order is Region, Total Count, Hospitals w/ Scores Count, Hospitals w/o Scores Count, Median Score
table_df = table_df.iloc[:, [0, 4, 3, 2, 1]]  # 'Region', 'Score', 'count' is original order

#Rename column headers
table_df = table_df.rename(columns={'Score': 'Median Score', 'count_x': 'Hospitals w/ Scores', 'count_y': 'Hospitals w/o Scores'})

#Sort the data frame from lowest to highest regional median score
table_df = table_df.sort_values('Median Score')

# Make a list of columns we'd like to sum for a "Totals" row
cols_to_sum = ['Total Hospitals', 'Hospitals w/o Scores', 'Hospitals w/ Scores']

#Add a totals row
totals = table_df[cols_to_sum].sum(numeric_only=True)

# Create a new name for the row
total_row = pd.Series(totals, name='Total')

#Add a 'Total' label at the end of the list of regions
total_row['Region'] = 'Total'

#Review what the table looks like
print("merged table", table_df)

# Append the totals row to the DataFrame
table_df.loc['Total'] = total_row


'''Generate Regional Data Table'''
# Apply styling to dataframe, this creates a styler object that will later need to be converted back into a dataframe

#First set the range for the choropleth values with the upper bound the rounded up maximum value
medianvmin = table_df['Median Score'].min()
medianvmax = table_df['Median Score'].max()

#Establish the caption styles before styling table
styles = [
        dict(selector="caption", props=[
            ("font-size", "20px"),
            ("padding-bottom", "13px"),
            ('text-align', 'left'),
            ('font-family', 'Helvetica')
            # Adjust this value to control height
        ])
    ]

#Establish a function to bold only the Totals row
def bold_row(row):
    # Example: Bold the row where 'Name' is 'Charlie'
    if row['Region'] == 'Total':
        return ['font-weight: bold'] * len(row)
    else:
        return [''] * len(row)

#Reset the index
table_df.reset_index(inplace=True, drop=True)

#Apply styling to the table_df dataframe.
#Hide the index for final output, align the text, format the median score to only include 2 decimal points
#set the background gradient to align with the map output figure and add a caption
#For future use to add caption: .set_caption('2023 Median MSPB Scores by U.S. Region')
styled_table_df =(table_df.style.hide(axis = "index").set_properties(**{'text-align':'center', 'font-size': '12pt'}).highlight_null(props="color: transparent;")
                  .format({'Total Hospitals':"{:,}",'Hospitals w/o Scores':"{:,}",'Hospitals w/ Scores':"{:,}",'Median Score': "{:.2f}"})
                  .background_gradient(axis = None, vmin =medianvmin, vmax=medianvmax,cmap=colormap, subset = pd.IndexSlice[0:5, 'Median Score'])
                  .set_caption('Table 1: 2023 Median U.S. Region MSPB Scores')).apply(bold_row, axis = 1).set_table_styles(styles)


# Export the styled DataFrame and use dpi = 400 for higher quality graphic and to match map
dfi.export(styled_table_df, '/Users/emilyquick-cole/Documents/Python/medicare_analysis/regional_table.png', dpi = 400)

'''Generate PDF functions '''
#Develop a letterhead function
def create_letterhead(letterhead, pdf):
    pdf.set_font('Helvetica', 'b', 20)
    pdf.multi_cell(0, 8, txt=letterhead, border=0, align='L', fill=0)
    #pdf.write(5, letterhead)
    pdf.ln(2)

    # Add date of report
    pdf.set_font('Helvetica', '', 10)
    #pdf.set_text_color(r=128, g=128, b=128)
    current_time = time.localtime()
    today = time.strftime("%B %d, %Y", current_time)
    pdf.write(4, f'{today}')
    pdf.ln(8)

#Develop a title function
def create_title(title, pdf):
    # Add main title
    pdf.set_font('Helvetica', 'b', 20)
    pdf.ln(40)
    pdf.write(5, title)
    pdf.ln(10)

    # Add date of report
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(r=128, g=128, b=128)
    current_time = time.localtime()
    today = time.strftime("%d/%m/%Y", current_time)
    pdf.write(4, f'{today}')

    # Add line break
    pdf.ln(10)

def create_subtitle(subtitle,pdf):
    pdf.set_font('Helvetica', 'BU', 12)
    pdf.write(5, subtitle)
    pdf.ln(8)

#Develop a function to add text to pdf
def write_to_pdf(pdf, words):
    # Set text colour, font size, and font type
    pdf.set_text_color(r=0, g=0, b=0)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5, txt = words, border=0, align='L', fill=0)
    #pdf.write(5, words)

class PDF(FPDF):

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')


'''Create the PDF'''
# Global Variables
TITLE = "Sample Data Report - Medicare Spending per Beneficiary Score (MPBS) Overview"
LETTERHEAD = "Sample Data Report - Medicare Spending per Beneficiary Score (MPBS) Overview"
WIDTH = 210
HEIGHT = 297
#Don't set a universal variable for subtitle because these will change throughout the report

# Create PDF
pdf = PDF() # A4 (210 by 297 mm)

'''First Page of PDF'''
# Add Page
pdf.add_page()

# Add letterhead and title
create_letterhead(LETTERHEAD, pdf)
#create_title(TITLE, pdf)

#Add a subtitle
create_subtitle('Background',pdf)

# Add some words to PDF
write_to_pdf(pdf, "Medicare is a U.S. federal health insurance program primarily for people age 65 or older, but also for younger individuals with certain disabilities, or other chronic conditions. It provides care coverage through different parts, such as Part A for hospital stays and hospice care and Part B for doctors' services and outpatient care.")
pdf.ln(5)

write_to_pdf(pdf, "According to the Centers for Medicaid and Medicare Services (CMS), the Medicare Spending Per Beneficiary (MSPB) Measure shows whether Medicare spends more, less, or about the same for an episode of care (episode) at a specific hospital compared to all hospitals nationally. An MSPB episode includes Medicare Part A and Part B payments for services provided by hospitals and other healthcare providers the 3 days prior to, during, and 30 days following a patient's inpatient stay. This measure evaluates hospitals' costs compared to the costs of the national median (or midpoint) hospital. This measure takes into account important factors like patient age and health status (risk adjustment) and geographic payment differences (payment-standardization).")
pdf.ln(5)

create_subtitle('Visuals and Findings',pdf)

# Add the generated visualisations to the PDF
pdf.image("/Users/emilyquick-cole/Documents/Python/medicare_analysis/regional_table.png", 10, 115, 95, 50) #WIDTH/2-10
pdf.image("/Users/emilyquick-cole/Documents/Python/medicare_analysis/MSPBmap.png", 105,115, 95)
pdf.ln(70)

#Bullet points on data
write_to_pdf(pdf, "- In 2023 4,530 hospitals across the U.S. received medicare patients. Of these, 2,909  from 49 different states reported MPBS scores. Eight states had a median MPBS score of 1.0, while 10 states' median scores were above 1.0, and 32 states' median scores were below 1.0.")
pdf.ln(2)
write_to_pdf(pdf, "- These hospitals are located in all regions of the U.S., with the most concentrated in the midwest (1,355), the south (1,137), and the west (811). The midwest and the south had the lowest median MSPB scores (0.97), while the mid-atlantic and the southwest had the greatest (1.01).")
pdf.ln(2)
write_to_pdf(pdf, "- Of the 4,591 hospitals, 1,621 hospitals did not report an MPBS. This may be because the hospitals did not meet the minimum number of beneficiary episodes (25), they had a significant number of episodes that are excluded for specific reasons, or the hospitals opted out of the Medicare program entirely.")
pdf.ln(5)
#To add another page: pdf.add_page()

#Add Conclusions
create_subtitle('Conclusions', pdf)
write_to_pdf(pdf, "A lower MSPB score suggests that a hospital or provider is more cost-efficient than the national average, while a higher score indicates higher spending. The score is used to affect a hospital's payments from Medicare. A higher MSPB score (meaning higher spending) can result in lower incentive payments or financial penalties. Overall, the MSPB measure is designed to identify variations in spending and to incentivize providers to deliver high-quality care in a more cost-effective manner.")
pdf.ln(2)

# Generate the PDF
pdf.output("/Users/emilyquick-cole/Documents/Python/medicare_analysis/2023MSPBReport.pdf", 'F')
