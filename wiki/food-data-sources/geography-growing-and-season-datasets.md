# Geography, Growing and Season Datasets

> Sources: Food Atlas source landscape research, 2026-09-17; Food Atlas pilot source review, 2026-09-17
> Raw: [Existing food atlases and datasets](../../raw/food-data-sources/2026-09-17-existing-food-atlases-and-datasets.md); [Pilot source review](../../raw/food-atlas-project/2026-09-17-pilot-source-review.md)
> Updated: 2026-09-17

## Overview

Three atlas layers depend on geography: where a food came from, where it grows now, and when it is in season. Origin and production have good open datasets. Growing requirements have one big FAO database with unclear terms. Consumer seasonality has no global dataset at all and must be curated country by country.

## Origin and domestication

- **Khoury et al. 2016** (Dryad, CC0) gives the primary regions of diversity for 151 crop commodities, linked to every country.
- **Meyer, DuVal & Jensen 2012** reviews 203 food crops with their domestication centre, wild ancestors, dates and traits.

A caution from the pilot review: a centre of diversity is not automatically a native range or a domestication origin, so these datasets answer a narrower question than where a food ultimately comes from.

## Growing requirements

- **FAO ECOCROP** holds environmental requirements for more than 2,000 plant species: temperature, rainfall, soil pH, light, Köppen zone, photoperiod and altitude.
- **GAEZ v4** (FAO and IIASA, 2021) adds land suitability and attainable yields.

Both remain cite-only for now: FAO's general reuse terms are non-commercial, and the ECOCROP landing page exposed no records when the pilot review tried to read one.

## Where food is grown

| Dataset | Content |
| :--- | :--- |
| **FAOSTAT** | Production by country and year, CC BY 4.0 |
| **CROPGRIDS** (Tang et al. 2024) | 173 crops, about 2020, on a 0.05° grid |
| **SPAM 2020** (IFPRI and WRI) | 46 crops on a 5 arc-minute grid, split by production system |
| **EarthStat / Monfreda et al. 2008** | 175 crops, about 2000 |

## Season

- **Sacks et al. 2010** provides gridded planting and harvest dates for 19 major crops.
- **WorldCereal** adds crop calendars for maize and wheat.
- **BZfE Saisonkalender** (Germany) covers about 75 fruit and vegetable types month by month, as a free app and an A3 PDF.
- **Everywhere else there is no dataset.** Consumer seasonality has to be curated from national calendars.

The pilot review adds a constraint for the German calendar: the BZfE website text is CC BY-NC-ND, and the calendar graphic's terms were not established, so months may be cited as single curated facts but the chart itself may not be reproduced. The review also flags an unresolved modelling question: whether a season claim means harvest or market availability.

## See Also

- [The food data landscape](food-data-landscape.md)
- [Pilot source review](../food-atlas-project/pilot-source-review.md)
- [Crop species and variety registers](crop-species-and-variety-registers.md)
