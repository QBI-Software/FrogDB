# -*- coding: utf-8 -*-
"""
Created on Mon May 30 12:50:43 2016

@author: lizcw_000
"""
from django import template
from ..models import Species

register = template.Library()
#################################################################################################
## Menu
@register.inclusion_tag('frogs/sp_submenu.html')
def show_speciesmenu():
    species = Species.objects.all()
    return {'species': species}