# -*- coding: utf-8 -*-
"""Diccionario y utilidades para macro sectores.

Este módulo centraliza el diccionario de macrosectores y
proporciona una función para identificar el macro sector al que
pertenece un sector específico. De esta forma el mismo diccionario
puede reutilizarse en las distintas páginas y gráficos de la
aplicación.
"""

from __future__ import annotations


def _normalize(name: str) -> str:
    """Normaliza nombres de sectores para coincidencias robustas."""
    if name is None:
        return ""
    name = name.casefold().strip().replace("-", " ").replace("/", " ")
    return " ".join(name.split())


macrosectores_dict = {
    "Social": [
        "Health", "Health education", "Health personnel development", "Health policy and administrative management",
        "Basic health care", "Basic health infrastructure", "Medical services", "Medical education/training",
        "Reproductive health care", "STD control including HIV/AIDS", "Malaria control", "Tuberculosis control",
        "Basic nutrition", "Family planning",
        "Education", "Education facilities and training", "Education policy and administrative management", "Early childhood education",
        "Higher education", "Lower secondary education", "Upper Secondary Education (modified and includes data from 11322)",
        "Teacher training", "Trade education/training", "Vocational training", "Educational research",
        "Basic life skills for youth", "Recreation and sport",
        "Social protection", "Social protection and welfare services policy, planning and administration",
        "Social services (incl youth development and women+ children)", "Civil service pensions", "General pensions"
    ],
    "Productivo": [
        "Agriculture, forestry and fishing", "Agricultural development", "Agricultural co-operatives", "Agricultural extension",
        "Agricultural education/training", "Agricultural inputs", "Agricultural land resources", "Agricultural alternative development",
        "Agricultural policy and administrative management", "Agricultural financial services", "Agricultural research", "Agricultural services",
        "Agricultural water resources", "Agro-industries", "Livestock", "Fishery development", "Fishery services", "Fishing policy and administrative management",
        "Forestry development", "Forestry policy and administrative management",
        "Industry, mining, construction", "Industrial development", "Industrial policy and administrative management", "Technological research and development",
        "Business policy and administration", "Small and medium-sized enterprises (SME) development",
        "Tourism policy and administrative management", "Responsible business conduct",
        "Banking and financial services", "Formal sector financial intermediaries", "Informal/semi-formal financial intermediaries", "Monetary institutions",
        "Financial policy and administrative management", "Retail gas distribution"
    ],
    "Infraestructura": [
        "Transport and storage", "Transport policy, planning and administration", "Transport regulation", "Feeder road construction", "National road construction",
        "Rail transport", "Water transport", "Air transport", "Public transport services",
        "Water supply and sanitation", "Water supply and sanitation - large systems", "Basic drinking water supply", "Basic drinking water supply and basic sanitation",
        "Basic sanitation", "Sanitation - large systems", "Waste management/disposal", "Water supply - large systems",
        "Electric power transmission and distribution (centralised grids)", "Energy generation and supply", "Energy generation, renewable sources - multiple technologies",
        "Energy sector policy, planning and administration", "Energy conservation and demand-side efficiency", "Hydro-electric power plants", "Geothermal energy",
        "Oil and gas (upstream)", "Solar energy for centralised grids", "Construction policy and administrative management",
        "Information and communication technology (ICT)", "Telecommunications", "Communications policy, planning and administration",
        "Urban development", "Urban land policy and management", "Rural development", "Rural land policy and management",
        "Low-cost housing", "Housing policy and administrative management", "Transport policy and administrative management"
    ],
    "Ambiental": [
        "Environmental policy and administrative management", "Environmental research", "Biodiversity", "Biosphere protection", "Flood prevention/control",
        "Disaster Risk Reduction", "Disaster prevention and preparedness", "Multi-hazard response preparedness",
        "Water resources conservation (including data collection)", "River basins development", "Site preservation"
    ],
    "Gobernanza/Público": [
        "Public sector policy and administrative management", "Budget planning", "General budget support-related aid",
        "Macroeconomic policy", "Debt and aid management", "Other general public services", "Other central transfers to institutions",
        "National monitoring and evaluation", "Justice, law and order policy, planning and administration", "Civilian peace-building, conflict prevention and resolution",
        "Security system management and reform", "Immigration", "Human rights", "Democratic participation and civil society",
        "Anti-corruption organisations and institutions", "Ending violence against women and girls", "Women's rights organisations and movements, and government institutions",
        "Foreign affairs", "Tax collection", "Tax policy and administration support", "Local government administration", "Local government finance",
        "Privatisation"
    ],
    "Multisectorial/Otros": [
        "Other multisector", "Sectors not specified", "Multisector aid for basic social services", "Immediate post-emergency reconstruction and rehabilitation",
        "Material relief assistance and services", "Relief co-ordination and support services"
    ]
}

# Crear un mapa normalizado para búsqueda rápida
_MACRO_LOOKUP = {
    _normalize(sector): macro
    for macro, sectors in macrosectores_dict.items()
    for sector in sectors
}


def get_macrosector(sector_name: str) -> str:
    """Retorna el macrosector correspondiente a un nombre de sector."""
    return _MACRO_LOOKUP.get(_normalize(sector_name), "No clasificado")

