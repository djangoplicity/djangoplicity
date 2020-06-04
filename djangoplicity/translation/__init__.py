# -*- coding: utf-8 -*-
#
# djangoplicity-translation
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the European Southern Observatory nor the names
#      of its contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY ESO ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL ESO BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE

"""
Django application for making multilingual applications. The application consists
of:

  * Middleware - A middleware that sets the active language based on a customisable
    URL prefix.
  * Multilingual model and managers.

Introduction
============
In general there are three main approaches for storing multilingual data in
a relational database (with various variations over the main approaches):

  * Use two tables - one for general non-translatable data and
    one for translatable data as a 1-N relation.
  * Use additional per language column for translatable data.
  * Use one table with new rows for translatable data.

All of them have trade-offs in terms of maintainability, storage efficiency, performance
and extensibility. For instance using two tables is easier to write, but harder to read due to
the joins involved between the two tables compared to e.g the per language column approach.

See http://scratchpad.wikia.com/wiki/Multilingual_Data_Structure for more information

The approach taken in this Django application is to store the multilingual data in one
table, having one source object and several translated objects with a reference to the source
object. The source object is responsible for storing all non-translatable data, however to
increase read performance, non-translatable data is replicated to the translated objects. This
is trivial for simple properties but causes some troubles for relations to other models,
especially when the other model is also multilingual. The problem is solved using some object managers
that are aware of the underlying data model.

The idea for the approach is taken from http://blog.rafaljonca.org/2009/03/third-style-of-django-multilingual-data.html

Concepts:

 * Default language: The default language for a website - that is, in case no
   language is specified, then this language is used. This is tied to the setting
   LANGUAGE_CODE.
 * Source instance: All translations have a source instance - i.e. this is the object
   that stores all the non-translatable properties of a model and that all the translation
   instances inherits. Note a source object can be in any of the supported languages - it
   doesn't necessarily needs to be in the default language.
 * Translation instance:
 * Property: A field stored on the model (e.g. a CharField - basically just relations are excluded)
 * Inherited property: This is a property which can *not* be translated - i.e. a translation instance
   inherits this property from the source instance. Example field: release_date.
 * Translated property: This is a property which can be translated - i.e. a translation instance
   must translate the property. Example field: title.
 * Non-inherited property: This is a property which is specific to the translation instance.
   Example: published.
 * Inherited relation
 * Non-inherited relation


Assumptions:
 *


Multilingual Model
==================
...
- Internal properties (source and lang)
- Translated properties
- Inherited properties
- Non-inherited properties
- Inherited relations
- Non-inherited relations


Relations and Mulilingual Models
================================
Multilingual models adds complexity to how relations are managed.


Relations To/From Multilingual Models
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
There are two types of one-to-many relations involving multilingual models:
  * Relations *from* the multilingual model
  * Relations *to* the multilingual model

A relation *from* a multilingual model to another model can just as normal
properties be:
  * inherited: translations inherit the relation from the source.
  * non-inherited: each translation must specify the relation.

Examples:
  * Item.type = ForeignKey( Type ) # Inherited
  * Item.template = ForeignKey( Template ) # Non-Inherited

A relation *to* a multilingual model from another model can allow for
  * source only relations: Only source instances can be related to the model.
  * all: Both source and translation instances can be related to the model.

Examples:
  * Image.item = ForeignKey( Item ) # Source only
  * Contact.item = ForeignKey( Item ) # All

*Special case*: Note, if you have two multilingual models m1 and m2, you could
create a non-inherited relation from m1 to all source and translation instances in
m2. This is however just a normal one-to-many relation between two normal models
(i.e. any m1 can be related to any m2).

Inherited Relations
^^^^^^^^^^^^^^^^^^^
An inherited relation is a relation defined from mulitlingual model to another
model where all translations inherit their source instance's relation. This is in
practice taken care of by copying the foreign key id from the source row to all
translation instance rows in the database. This happens every time a source is saved.

This means that SQL queries get's simpler, we can do with less queries, and we don't
need to modify too much of Django's behavior.

Multilingual One-to-Many Relations
----------------------------------
Consider the relations:

An Item has one Type <=> A Type has many Items # Inherited, From multilingual model
An Item has one Template <=> A Template has many Items # Non-inherited, From multilingual model
An Item has many Images <=> An Image as one Item # Source only, To multilingual model
An Item has many Contacts <=> A Contact as one Item # All, To multilingual model

In Django the above relations will result in the following forward relation
managers on an model instance:

  * item.type
  * item.template
  * image.item
  * contact.item

and the following reverse relation managers:

  * type.item_set
  * template.item_set
  * item.image_set
  * item.contact_set

Forward Relationships
^^^^^^^^^^^^^^^^^^^^^
Forward relationship managers are not dependent on if the object instance is a source
or translation instance as the forward relationships managers uses the inherited relation
which has been copied from the source.

.. warning: You should however at the moment not assign values to a forward relationship in a translation
instances if the forward relationship is inherited. E.g. item.type = Type(..) is ok if item is a source,
but *not if item is a translation*. Also item.tempalte = Template(...) is ok for both source and translation
as template is a non-inherited relation.

  * item.type (inherited, from): Return the type where type.pk=item.type_id
  * item.template (non-inherited, from): Return the template where template.pk=item.template_id
  * image.item (source only, to): Return the item where item.pk=image.item_id
  * contact.item (all, to): Return the item where item.pk=contact.item_id

Reverse Relationships
^^^^^^^^^^^^^^^^^^^^^
Reverse relationship managers are dependent on if the object is a source or translation instance.

Source instance:
  * type.item_set (inherited, from): Return all items where item.type_id=type.pk and item.source=null
  * template.item_set (non-inherited, from): Return all items where item.template_id=template.pk
  * item.image_set (source only, to): Return all images where image.item_id=item.pk and item.source=null
  * item.contact_set (all, to): Return all contacts where contact.item_id=item.pk

Translation instance:
  * type.item_set (inherited, from): No No difference from source instance
  * template.item_set (non-inherited, from): No difference from source instance
  * item.image_set (source only, to): Return all images where image.item_id=item.source.pk and item.source=null
  * item.contact_set (all, to): No difference from source instance

Important Notes
===============
   * In case Django is updated, djangoplicity.translation.fields needs to be checked to see if there's any
     changes to corresponding methods.

Usage
=====
To use the multilingual features in a project you need to do the following:

   * Ensure that django-rosetta is installed and configured (added to urls.py and INSTALLED_APPS in settings.py)
   * Make sure that to set LANGUAGES, DEFAULT_PREFIX, LANGUAGE_PREFIX, USE_I18N, USE_L10N and LOCALE_PATHS settings variables.
   * Add rosetta and djangoplicity.translation to INSTALLED_APPS
   * All multilingual views must be specified with view_kwargs { 'translate' : True, ... }
   * Add djangoplicity.translation.middleware.LocaleMiddleware to you list of middleware.
   * Create a new Fabric task for the project using djangoplicity.fabric.makemessages.
   * Generate locale message for the you language, either by "fab makemessages" or "django-admin.py makemessages -l da"


Multi-lingual archives
======================
To make an existing archive multi-lingual, please follow this non-exhaustive list of things that must be done:

    * (!) Subclass model from TranslationModel instead of models.Model
    * (!) Add class Translation( object ) to you model class with the two attributes fields and excludes.
    * (!) Check all ForeignKeys/ManyToManyField to and from the model. Leave or change them into either
      TranslationForeignKey, TranslationManyToManyField. Use <model>._meta to check all fks and m2ms
      as well as the <model>.Archive.Meta.rename_fks
    * Make sure (<model table>,'source_id') is added to <model>.Archive.Meta.rename_fks
    * (!) Change <model>.get_absolute_url() to use translation.moddels.translation_reverse() instead of reverse()
      and pass it the 'lang' attribute
    * Add a proxy model for model to allow admin editing (see releases/images). Proxy model should automatically
      compute id, and validate language and ID (done through a Mixin class. Please check that automatic id generation does not
      conflict with existing ids.
    * Admin:
        * Add inline proxy model admin and proxy admin
        * Add button "Translations" to templates/admin/<app>/<model>/change_form.html for model detail admin.
        * Add button "Original" to templates/admin/<app>/<modelproxy>/change_form.html for model detail admin.
        * Register proxy admin
    * (!) Options (options.py):
        * Mark translations strings with ungettext_noop (this is a larger task to find all strings).
        * Fix admin edit link
        * Add translations to extra_context() if the method has been override (for flags on detail page)
        * All info functions used in "About the object" etc. should have a translatable short_description
    * (!) The projects urls.py must include { 'translate' : True } as args to the view.
    * If model has a serializer be sure to add the language to the serializer.
    * Public templates:
        * Make sure archives/translations.html is included in object_description.html to add flags.
    * (!) Last things to do:
        * Extract messages (fab -f fabfile_old.py makemessages / fab -f fabfile_old.py updatemessages / fab -f fabfile_old.py compilemessages)
        * Make south migrations
"""
