# gpw-v4-population-count-adjusted-to-2015-unwpp-country-totals_2015.tif comes from 477MB download at:
# http://beta.sedac.ciesin.columbia.edu/data/set/gpw-v4-population-count-adjusted-to-2015-unwpp-country-totals/data-download

gpwv4-2015.csv.gz: gpw-v4-population-count-adjusted-to-2015-unwpp-country-totals-2015/gpw-v4-population-count-adjusted-to-2015-unwpp-country-totals_2015.tif \
     gl_grumpv1_ntlbndid_grid_30/gluntlbnds gluntlbnds.csv
	./reduce-gpwv4.py gpw-v4-population-count-adjusted-to-2015-unwpp-country-totals-2015/gpw-v4-population-count-adjusted-to-2015-unwpp-country-totals_2015.tif \
	                  gl_grumpv1_ntlbndid_grid_30/gluntlbnds gluntlbnds.csv $@

# gl_grumpv1_ntlbndid_grid_30/gluntlbnds comes from 9.7MB grid download at:
# http://sedac.ciesin.columbia.edu/data/set/grump-v1-national-identifier-grid/data-download

gluntlbnds.csv: gl_grumpv1_ntlbndid_grid_30/gluntlbnds
	./extract-lookup.py gl_grumpv1_ntlbndid_grid_30/gluntlbnds $@

# Gecon40_post_final.xls comes from 17.5MB XLS download at:
# http://gecon.yale.edu/data-and-documentation-g-econ-project

gecon.csv.gz: Gecon40_post_final.xls
	./cut-gecon.py Gecon40_post_final.xls $@
