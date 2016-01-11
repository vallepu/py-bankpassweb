# Introduction #

This page details the process of installing the BankPass module for Satchmo. Previous knowledge of Satchmo and Django is very helpful and possibly required. :)

# Procedure #

  1. Install the `bankpassweb` module by means of the included `setup.py` (setuptools) script.
  1. Edit the `settings` module for your Satchmo installation. Its contents are usually located in the `settings.py` and `local_settings.py` files. Add `bankpassweb.satchmo_payment` to the `INSTALLED_APPS` tuple and to the `CUSTOM_PAYMENT_MODULES` tuple or list.
  1. Enter the settings web page for your Satchmo installation. This is usually located at `http://www.yoursite.com/settings/`. Enable "BankPass Web" in the _Enable payment modules_ list, then save.
  1. The page will reload with the _BankPass Web Payment Settings_. Enter the personal configuration data you were provided by the bank (for the live settings) and/or by e-Display (for the test settings). You have to set the CRN (shop ID), "chiave di avvio" (transaction key), "chiave di esito/API" (result key). Save the settings.

You're ready!