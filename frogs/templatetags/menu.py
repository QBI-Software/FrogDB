# -*- coding: utf-8 -*-
"""
Created on Mon May 30 12:50:43 2016

@author: lizcw_000
"""
from django import template
#from frogs.models import Species

register = template.Library()
#################################################################################################
## Menu
@register.inclusion_tag('sp_submenu.html')
def show_speciesmenu():
    species = ['X.borealis','X.laevis']
    return {'species': species}