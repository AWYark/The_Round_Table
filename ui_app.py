import os
import refresh_price
import vendor_booth

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle


from authentication import register_user, login_user
from view_inventory import (load_inventory, update_card_details, remove_inventory_entry, remove_one_copy,)
from scanner2 import run_scanner
from inventory_store import add_card_to_inventory
from card_summary import CONDITION_MULTIPLIERS, NZD_PER_USD


KV = """
ScreenManager:
    LoginScreen:
    RegisterScreen:
    DashboardScreen:
    InventoryScreen:
    EditCardScreen:
    ScannerScreen:
    VendorScreen:


<LoginScreen>:
    name: "login"

    BoxLayout:
        orientation: "vertical"
        padding: 30
        spacing: 15

        Widget:
            size_hint_y: 0.3

        Label:
            text: "THE ROUND TABLE"
            font_size: "30sp"
            bold: True
            size_hint_y: None
            height: "60dp"

        Label:
            text: "MTG Inventory & Marketplace"
            font_size: "16sp"
            size_hint_y: None
            height: "35dp"

        TextInput:
            id: username
            hint_text: "Username or email"
            multiline: False
            size_hint_y: None
            height: "50dp"

        TextInput:
            id: password
            hint_text: "Password"
            password: True
            multiline: False
            size_hint_y: None
            height: "50dp"

        Button:
            text: "LOGIN"
            size_hint_y: None
            height: "50dp"
            on_release: root.login()

        Button:
            text: "REGISTER"
            size_hint_y: None
            height: "50dp"
            on_release: root.manager.current = "register"

        Label:
            id: message
            text: "Welcome to The Round Table"
            size_hint_y: None
            height: "40dp"

        Widget:
            size_hint_y: 0.3


<RegisterScreen>:
    name: "register"

    BoxLayout:
        orientation: "vertical"
        padding: 30
        spacing: 10

        Label:
            text: "CREATE ACCOUNT"
            font_size: "26sp"
            bold: True
            size_hint_y: None
            height: "55dp"

        TextInput:
            id: display_name
            hint_text: "Display name"
            multiline: False

        TextInput:
            id: username
            hint_text: "Username (3-24 characters)"
            multiline: False

        TextInput:
            id: email
            hint_text: "Email address"
            multiline: False

        TextInput:
            id: password
            hint_text: "Password (minimum 12 characters)"
            password: True
            multiline: False

        TextInput:
            id: confirm_password
            hint_text: "Confirm password"
            password: True
            multiline: False

        Button:
            text: "CREATE ACCOUNT"
            size_hint_y: None
            height: "50dp"
            on_release: root.register()

        Button:
            text: "BACK TO LOGIN"
            size_hint_y: None
            height: "50dp"
            on_release: root.back_to_login()

        Label:
            id: message
            text: ""
            size_hint_y: None
            height: "55dp"


<DashboardScreen>:
    name: "dashboard"

    BoxLayout:
        orientation: "vertical"
        padding: 30
        spacing: 15

        Label:
            id: welcome
            text: "Welcome!"
            font_size: "26sp"
            bold: True

        Label:
            id: account_info
            text: ""
            font_size: "14sp"

        Button:
            text: "VIEW INVENTORY"
            size_hint_y: None
            height: "55dp"
            on_release: root.open_inventory()

        Button:
            text: "VENDOR MARKETPLACE"
            size_hint_y: None
            height: "55dp"
            on_release: root.open_vendor()

        Button:
            text: "SCAN A CARD"
            size_hint_y: None
            height: "55dp"
            on_release: root.open_scanner()

        Widget:

        Button:
            text: "LOG OUT"
            size_hint_y: None
            height: "50dp"
            on_release: root.logout()
            
<InventoryScreen>:
    name: "inventory"

    BoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 10

        Label:
            text: "MY MTG INVENTORY"
            font_size: "24sp"
            bold: True
            size_hint_y: None
            height: "50dp"

        Label:
            id: inventory_summary
            text: "Loading inventory..."
            size_hint_y: None
            height: "40dp"

        TextInput:
            id: search_input
            hint_text: "Search card name, set name or set code..."
            multiline: False
            size_hint_y: None
            height: "30dp"
            on_text: root.search_inventory(self.text)

        Spinner:
            id: condition_filter
            text: "All Conditions"
            values: ["All Conditions", "Near Mint", "Lightly Played", "Moderately Played", "Heavily Played", "Damaged"]
            size_hint_y: None
            height: "30dp"
            on_text: root.search_inventory(search_input.text)

        Spinner:
            id: foil_filter
            text: "All"
            values: ["All", "Foil", "Non-foil"]
            size_hint_y: None
            height: "30dp"
            on_text: root.search_inventory(search_input.text)
        
        Button:
            text: "CLEAR SEARCH"
            size_hint_y: None
            height: "30dp"
            on_release: root.clear_search()

        ScrollView:
            id: inventory_scroll
            do_scroll_x: False

            GridLayout:
                id: card_list
                cols: 2
                spacing: 10
                size_hint_y: None
                height: self.minimum_height

        Button:
            text: "BACK TO DASHBOARD"
            size_hint_y: None
            height: "50dp"
            on_release: root.manager.current = "dashboard"
            
<EditCardScreen>:
    name: "edit_card"

    BoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 12

        Label:
            id: card_title
            text: "EDIT CARD"
            font_size: "24sp"
            bold: True
            size_hint_y: None
            height: "50dp"

        Label:
            text: "Card condition"
            size_hint_y: None
            height: "30dp"

        Spinner:
            id: condition
            text: "Near Mint"
            values: ["Near Mint","Lightly Played","Moderately Played","Heavily Played","Damaged"]
            size_hint_y: None
            height: "50dp"

        Label:
            text: "Foil status"
            size_hint_y: None
            height: "30dp"

        Spinner:
            id: foil
            text: "No"
            values: ["No", "Yes"]
            size_hint_y: None
            height: "50dp"
            
        Label:
            text: "Quantity"
            size_hint_y: None
            height: "30dp"

        TextInput:
            id: quantity
            text: "1"
            multiline: False
            input_filter: "int"
            size_hint_y: None
            height: "50dp"

        Label:
            id: edit_message
            text: ""
            size_hint_y: None
            height: "50dp"

        Button:
            text: "SAVE CHANGES"
            size_hint_y: None
            height: "50dp"
            on_release: root.save_changes()

        Button:
            text: "CANCEL"
            size_hint_y: None
            height: "50dp"
            on_release: root.manager.current = "inventory"
            
<ScannerScreen>:
    name: "scanner"

    BoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 15

        Label:
            text: "MTG CARD SCANNER"
            font_size: "26sp"
            bold: True
            size_hint_y: None
            height: "55dp"

        Label:
            id: scanner_message
            text: "Select a card image to begin."
            size_hint_y: None
            height: "50dp"

        Image:
            id: card_preview
            source: ""
            size_hint_y: 0.55
            allow_stretch: True
            keep_ratio: True

        Button:
            text: "SELECT CARD IMAGE"
            size_hint_y: None
            height: "55dp"
            on_release: root.open_file_chooser()

        Button:
            text: "SCAN CARD"
            size_hint_y: None
            height: "55dp"
            on_release: root.scan_card()

        Widget:

        Button:
            text: "BACK TO DASHBOARD"
            size_hint_y: None
            height: "50dp"
            on_release: root.manager.current = "dashboard"

<VendorScreen>:
    name: "vendor"

    BoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 10

        Label:
            text: "VENDOR MARKETPLACE"
            font_size: "24sp"
            size_hint_y: None
            height: "55dp"

        Button:
            text: "MY LISTINGS"
            size_hint_y: None
            height: "50dp"
            on_release: root.show_my_listings()

        Button:
            text: "CREATE LISTING"
            size_hint_y: None
            height: "50dp"
            on_release: root.open_create_listing()

        Button:
            text: "BROWSE MARKETPLACE"
            size_hint_y: None
            height: "50dp"
            on_release: root.open_browse_marketplace()

        Button:
            text: "MY ENQUIRIES"
            size_hint_y: None
            height: "50dp"
            on_release: root.show_my_enquiries()

        ScrollView:
            do_scroll_x: False

            GridLayout:
                id: listings_container
                cols: 1
                spacing: 8
                size_hint_y: None
                height: self.minimum_height

        Label:
            id: vendor_message
            text: "Select an option above."
            size_hint_y: None
            height: "45dp"

        Button:
            text: "BACK TO DASHBOARD"
            size_hint_y: None
            height: "50dp"
            on_release: root.manager.current = "dashboard"
            
"""

class ListingRow(ButtonBehavior, BoxLayout):
    """A tappable row that behaves like a button but can hold several widgets."""

    NORMAL_COLOR = (0.16, 0.20, 0.28, 1)
    PRESSED_COLOR = (0.24, 0.30, 0.42, 1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self._bg_color = Color(*self.NORMAL_COLOR)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(
            pos=self._update_background,
            size=self._update_background,
            state=self._update_color,
        )

    def _update_background(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _update_color(self, *_):
        self._bg_color.rgba = (
            self.PRESSED_COLOR if self.state == "down" else self.NORMAL_COLOR
        )

class LoginScreen(Screen):

    def login(self):
        identifier = self.ids.username.text.strip()
        password = self.ids.password.text

        if not identifier or not password:
            self.ids.message.text = "Enter your username and password."
            return

        try:
            result = login_user(identifier, password)

            if result["success"]:
                app = App.get_running_app()
                app.current_user = result["user"]

                self.ids.password.text = ""
                self.ids.message.text = ""

                self.manager.current = "dashboard"

            else:
                self.ids.message.text = result["message"]

        except Exception as error:
            print("Login error:", error)
            self.ids.message.text = "Unable to connect. Please try again."

class RegisterScreen(Screen):

    def register(self):
        display_name = self.ids.display_name.text.strip()
        username = self.ids.username.text.strip()
        email = self.ids.email.text.strip()
        password = self.ids.password.text
        confirm_password = self.ids.confirm_password.text

        if not all([display_name, username, email, password, confirm_password]):
            self.ids.message.text = "Please complete every field."
            return

        if password != confirm_password:
            self.ids.message.text = "Passwords do not match."
            return

        if len(password) < 12:
            self.ids.message.text = "Password must be at least 12 characters."
            return

        if len(password.encode("utf-8")) > 72:
            self.ids.message.text = "Password exceeds the 72-byte limit."
            return

        try:
            result = register_user(
                username,
                email,
                password,
                display_name
            )

            self.ids.message.text = result["message"]

            if result["success"]:
                self.ids.display_name.text = ""
                self.ids.username.text = ""
                self.ids.email.text = ""
                self.ids.password.text = ""
                self.ids.confirm_password.text = ""

                self.manager.current = "login"

                login_screen = self.manager.get_screen("login")
                login_screen.ids.message.text = (
                    "Account created! Please log in."
                )

        except Exception as error:
            print("Registration error:", error)
            self.ids.message.text = "Registration failed. Please try again."

    def back_to_login(self):
        self.manager.current = "login"

class DashboardScreen(Screen):

    def on_pre_enter(self):
        app = App.get_running_app()
        user = app.current_user

        if user:
            self.ids.welcome.text = (
                f"Welcome, {user['display_name']}!"
            )

            self.ids.account_info.text = (
                f"Username: {user['username']}\n"
                f"Account type: {user['account_type']}"
            )
            

    def open_inventory(self):
        app = App.get_running_app()
        user = app.current_user

        try:
            if user and user.get("owner_id"):
                owner_id = user["owner_id"]

                print("\nRefreshing your inventory prices...")
                refresh_price.main(owner_id=owner_id)

        except Exception as error:
            print(f"Price refresh failed: {error}")
            print("Opening inventory without refreshed prices.")

        finally:
            self.manager.current = "inventory"
        
    def open_scanner(self):
        self.manager.current = "scanner"
        
    def open_vendor(self):
        self.manager.current = "vendor"

    def logout(self):
        App.get_running_app().current_user = None
        self.manager.current = "login"

class InventoryScreen(Screen):

    def on_pre_enter(self):
        self.refresh_inventory() 

    def refresh_inventory(self):
        app = App.get_running_app()
        user = app.current_user

        if not user or not user.get("owner_id"):
            self.all_cards = []
            self.ids.inventory_summary.text = "Please log in again."
            return

        owner_id = user["owner_id"]

        try:
            self.all_cards = load_inventory(owner_id)
            self.search_inventory(self.ids.search_input.text)

        except Exception as error:
            print("Inventory loading error:", error)

            self.all_cards = []
            self.ids.inventory_summary.text = "Unable to load inventory."

    def search_inventory(self, search_term):
        cards = getattr(self, "all_cards", [])

        term = search_term.strip().casefold()

        condition_filter = self.ids.condition_filter.text
        foil_filter = self.ids.foil_filter.text

        filtered_cards = []

        for card in cards:
            card_name = str(card.get("name", "")).casefold()
            set_name = str(card.get("set_name", "")).casefold()
            set_code = str(card.get("set", "")).casefold()

            # Search card name, set name and set code.
            if term and not any(
                term in value
                for value in (card_name, set_name, set_code)
            ):
                continue

            # Filter by card condition.
            if (
                condition_filter != "All Conditions"
                and card.get("condition", "Near Mint") != condition_filter
            ):
                continue

            # Filter by foil status.
            is_foil = bool(card.get("foil", False))

            if foil_filter == "Foil" and not is_foil:
                continue

            if foil_filter == "Non-foil" and is_foil:
                continue

            filtered_cards.append(card)
        
        if not filtered_cards:
            self.ids.card_list.clear_widgets()

            if term:
                self.ids.inventory_summary.text = "No matching cards found."
                message = f'No cards matching "{term}" were found.'
            else:
                self.ids.inventory_summary.text = "Your inventory is empty."
                message = "No cards have been added to your inventory yet."

            self.ids.card_list.add_widget(
                Label(
                    text=message,
                    size_hint_y=None,
                    height=60,
                )
            )
            return


        total_copies = 0
        priced_copies = 0
        missing_price_copies = 0
        total_value_nzd = 0.0

        for card in filtered_cards:
            try:
                quantity = int(card.get("quantity", 1))
            except (TypeError, ValueError):
                quantity = 1

            total_copies += quantity

            prices = card.get("prices") or {}

            if card.get("foil", False):
                market_price = prices.get("usd_foil")
            else:
                market_price = prices.get("usd")

            if market_price is None or market_price == "":
                market_price = prices.get("usd")

            try:
                base_price_usd = float(market_price)

                condition = card.get("condition", "Near Mint")
                multiplier = CONDITION_MULTIPLIERS.get(
                    condition,
                    1.00,
                )

                adjusted_price_nzd = (
                    base_price_usd
                    * multiplier
                    * NZD_PER_USD
                )

                total_value_nzd += adjusted_price_nzd * quantity
                priced_copies += quantity

            except (ValueError, TypeError):
                missing_price_copies += quantity

        self.ids.inventory_summary.text = (
            f"{len(filtered_cards)} unique entries | "
            f"{total_copies} total copies\n"
            f"Estimated inventory value: NZD {total_value_nzd:.2f}\n"
            f"Priced copies: {priced_copies} | "
            f"Missing prices: {missing_price_copies}"
        )

        self.ids.card_list.clear_widgets()

        for card in filtered_cards:
            card_name = card.get("name", "Unknown card")
            set_name = card.get("set_name", "Unknown set")
            set_code = str(card.get("set", "??")).upper()
            collector = card.get("collector_number", "??")
            condition = card.get("condition", "Near Mint")
            foil = "Yes" if card.get("foil", False) else "No"
            quantity = card.get("quantity", 1)
            
            # Calculate the estimated card value.
            prices = card.get("prices") or {}

            if card.get("foil", False):
                market_price = prices.get("usd_foil")
            else:
                market_price = prices.get("usd")

            # Fall back to non-foil pricing if foil pricing is unavailable.
            if market_price is None or market_price == "":
                market_price = prices.get("usd")

            try:
                base_price_usd = float(market_price)
                multiplier = CONDITION_MULTIPLIERS.get(
                    condition,
                    1.00,
                )

                adjusted_price_nzd = (
                    base_price_usd
                    * multiplier
                    * NZD_PER_USD
                )

                total_value_nzd = adjusted_price_nzd * int(quantity)

                price_text = (
                    f"Market : USD {base_price_usd:.2f}\n"
                    f"Per card: "
                    f"NZD {adjusted_price_nzd:.2f}\n"
                    f"Estimated value: "
                    f"NZD {total_value_nzd:.2f}"
                )

            except (ValueError, TypeError):
                price_text = "Estimated value: Unavailable"

            card_box = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=260,
                spacing=5,
                padding=10,
            )

            card_box.add_widget(
                Label(
                    text=(
                        f"{card_name}\n"
                        f"{set_name} ({set_code})\n"
                        f"Collector: {collector}\n"
                        f"Condition: {condition}\n"
                        f"Foil: {foil} | Quantity: {quantity}\n\n"
                        f"{price_text}\n"
                    ),
                    size_hint_y=None,
                    height=175,
                    halign="left",
                    valign="middle",
                    text_size=(None, None),
                )
            )

            action_row = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=45,
                spacing=8,
            )

            edit_button = Button(
                text="EDIT CARD",
                size_hint_x=0.5,
            )

            edit_button.bind(
                on_release=lambda instance, selected_card=card:
                self.open_edit_screen(selected_card)
            )

            remove_button = Button(
                text="REMOVE CARD",
                size_hint_x=0.5,
            )

            remove_button.bind(
                on_release=lambda instance, selected_card=card:
                self.confirm_remove_card(selected_card)
            )

            action_row.add_widget(edit_button)
            action_row.add_widget(remove_button)
            card_box.add_widget(action_row)
            
            self.ids.card_list.add_widget(card_box)
        
        self.ids.inventory_scroll.scroll_y = 1
    
    def open_edit_screen(self, card):
        edit_screen = self.manager.get_screen("edit_card")
        edit_screen.load_card(card)
        self.manager.current = "edit_card"
        
    def confirm_remove_card(self, card):
        card_name = card.get("name", "Unknown card")
        quantity = card.get("quantity", 1)

        content = BoxLayout(
            orientation="vertical",
            spacing=12,
            padding=12,
        )

        message = Label(
            text=(
                f"Remove copies of {card_name}?\n\n"
                f"Current quantity: {quantity}\n\n"
                "Remove one copy to reduce the quantity by 1.\n"
                "Remove entire entry to delete all copies.\n\n"
                "If only one copy remains, removing one copy "
                "will remove the entire entry."
            ),
            halign="center",
            valign="middle",
        )

        content.add_widget(message)

        action_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=45,
            spacing=10,
        )

        remove_one_button = Button(text="REMOVE ONE COPY")
        remove_all_button = Button(text="REMOVE ENTIRE ENTRY")

        cancel_button = Button(
            text="CANCEL",
            size_hint_y=None,
            height=45,
        )

        action_row.add_widget(remove_one_button)
        action_row.add_widget(remove_all_button)

        content.add_widget(action_row)
        content.add_widget(cancel_button)

        popup = Popup(
            title="Confirm card removal",
            content=content,
            size_hint=(0.9, 0.5),
            auto_dismiss=False,
        )

        cancel_button.bind(
            on_release=lambda instance: popup.dismiss()
        )

        def remove_selected_card(instance, removal_function):
            app = App.get_running_app()
            user = app.current_user

            if not user or not user.get("owner_id"):
                popup.dismiss()
                self.ids.inventory_summary.text = (
                    "Please log in again."
                )
                return

            result = removal_function(
                card,
                user["owner_id"],
            )

            popup.dismiss()

            if result["success"]:
                self.refresh_inventory()

            self.ids.inventory_summary.text = result["message"]

        remove_one_button.bind(
            on_release=lambda instance: remove_selected_card(
                instance,
                remove_one_copy,
            )
        )

        remove_all_button.bind(
            on_release=lambda instance: remove_selected_card(
                instance,
                remove_inventory_entry,
            )
        )

        popup.open()

    def clear_search(self):
        self.ids.search_input.text = ""

    def logout(self):
        App.get_running_app().current_user = None
        self.manager.current = "login"

class ScannerScreen(Screen):

    def open_file_chooser(self):
        chooser = FileChooserListView(
            filters=["*.png", "*.jpg", "*.jpeg"],
            dirselect=False
        )

        buttons = BoxLayout(
            size_hint_y=None,
            height="45dp",
            spacing=10
        )

        select_button = Button(text="SELECT")
        cancel_button = Button(text="CANCEL")

        buttons.add_widget(select_button)
        buttons.add_widget(cancel_button)

        content = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=10
        )

        content.add_widget(chooser)
        content.add_widget(buttons)

        self.file_popup = Popup(
            title="Choose MTG Card Image",
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=False
        )

        select_button.bind(
            on_release=lambda *_: self.select_image(chooser.selection)
        )

        cancel_button.bind(
            on_release=lambda *_: self.file_popup.dismiss()
        )

        self.file_popup.open()

    def select_image(self, selection):
        if not selection:
            self.ids.scanner_message.text = (
                "Please select an image first."
            )
            return

        self.selected_image_path = selection[0]

        self.ids.card_preview.source = self.selected_image_path
        self.ids.card_preview.reload()

        self.ids.scanner_message.text = (
            "Card image selected successfully."
        )

        self.file_popup.dismiss()
        
    def scan_card(self):
        app = App.get_running_app()
        user = app.current_user

        if not user or not user.get("owner_id"):
            self.ids.scanner_message.text = "Please log in again."
            return

        if not getattr(self, "selected_image_path", None):
            self.ids.scanner_message.text = "Please select a card image first."
            return

        self.ids.scanner_message.text = "Scanning card... Please wait."

        try:
            result = run_scanner(
                user["owner_id"],
                image_path=self.selected_image_path,
                interactive=False
            )

            if result:
                card_name = result.get("name", "Unknown card")
                set_code = result.get("set", "Unknown set")
                collector_number = result.get(
                    "collector_number", "Unknown"
                )

                self.ids.scanner_message.text = (
                    f"Verified: {card_name}\n"
                    f"{set_code.upper()} / {collector_number}"
                )

                self.show_save_confirmation(
                    result,
                    user["owner_id"]
                )
            else:
                self.ids.scanner_message.text = (
                    "Card could not be verified. "
                    "Check the scanner output."
                )

        except Exception as error:
            self.ids.scanner_message.text = (
                f"Scanner error: {error}"
            )
            print(f"Scanner error: {error}")
            

    def show_save_confirmation(self, card, owner_id):
        self.pending_verified_card = card
        self.pending_owner_id = owner_id

        card_name = card.get("name", "Unknown card")
        set_code = str(card.get("set", "??")).upper()
        collector = card.get("collector_number", "??")
        set_name = card.get("set_name", "Unknown set")

        content = BoxLayout(
            orientation="vertical",
            padding=15,
            spacing=10,
        )

        details = Label(
            text=(
                f"Verified card:\n"
                f"{card_name}\n"
                f"{set_name}\n"
                f"{set_code} / {collector}"
            ),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height="100dp",
        )
        content.add_widget(details)

        content.add_widget(
            Label(
                text="Card condition:",
                size_hint_y=None,
                height="30dp",
            )
        )

        self.condition_spinner = Spinner(
            text="Near Mint",
            values=(
                "Near Mint",
                "Lightly Played",
                "Moderately Played",
                "Heavily Played",
                "Damaged",
            ),
            size_hint_y=None,
            height="45dp",
        )
        content.add_widget(self.condition_spinner)

        content.add_widget(
            Label(
                text="Foil status:",
                size_hint_y=None,
                height="30dp",
            )
        )

        self.foil_spinner = Spinner(
            text="Non-foil",
            values=("Non-foil", "Foil"),
            size_hint_y=None,
            height="45dp",
        )
        content.add_widget(self.foil_spinner)

        buttons = BoxLayout(
            size_hint_y=None,
            height="50dp",
            spacing=10,
        )

        save_button = Button(text="SAVE TO INVENTORY")
        cancel_button = Button(text="CANCEL")

        buttons.add_widget(save_button)
        buttons.add_widget(cancel_button)
        content.add_widget(buttons)

        self.confirmation_popup = Popup(
            title="Confirm Inventory Addition",
            content=content,
            size_hint=(0.9, 0.8),
            auto_dismiss=False,
        )

        save_button.bind(
            on_release=lambda *_: self.confirm_save_card()
        )

        cancel_button.bind(
            on_release=lambda *_: self.cancel_save_card()
        )

        self.confirmation_popup.open()

    def cancel_save_card(self):
        self.pending_verified_card = None
        self.pending_owner_id = None

        self.confirmation_popup.dismiss()

        self.ids.scanner_message.text = (
            "Verified card was not added to inventory."
        )

    def confirm_save_card(self):
        app = App.get_running_app()
        user = app.current_user

        if not user or not user.get("owner_id"):
            self.confirmation_popup.dismiss()
            self.ids.scanner_message.text = "Please log in again."
            return

        if user["owner_id"] != self.pending_owner_id:
            self.confirmation_popup.dismiss()
            self.ids.scanner_message.text = (
                "Account changed. Please scan the card again."
            )
            return

        try:
            card = self.pending_verified_card
            owner_id = self.pending_owner_id
            condition = self.condition_spinner.text
            foil = self.foil_spinner.text == "Foil"

            if os.getenv(
                "INVENTORY_BACKEND", "json"
            ).strip().lower() == "mongodb":

                add_card_to_inventory(
                    card,
                    owner_id=owner_id,
                    condition=condition,
                    foil=foil,
                )

            else:
                add_card_to_inventory(
                    card,
                    condition=condition,
                    foil=foil,
    )

            self.confirmation_popup.dismiss()

            self.pending_verified_card = None
            self.pending_owner_id = None

            self.ids.scanner_message.text = (
                f"Added {card.get('name')} to inventory.\n"
                f"Condition: {condition} | Foil: {'Yes' if foil else 'No'}"
            )

            inventory_screen = self.manager.get_screen("inventory")
            inventory_screen.refresh_inventory()

            self.manager.current = "inventory"

        except Exception as error:
            self.confirmation_popup.dismiss()

            self.ids.scanner_message.text = (
                f"Inventory save failed: {error}"
            )

            print("Inventory save error:", error)

class EditCardScreen(Screen):

    def load_card(self, card):
        self.card = card

        self.ids.card_title.text = (
            f"EDIT: {card.get('name', 'Unknown card')}"
        )

        self.ids.condition.text = card.get(
            "condition", "Near Mint"
        )

        self.ids.foil.text = (
            "Yes" if card.get("foil", False) else "No"
        )

        self.ids.quantity.text = str(
            card.get("quantity", 1)
        )
    
        self.ids.edit_message.text = ""

    def save_changes(self):
        app = App.get_running_app()
        user = app.current_user

        if not user or not user.get("owner_id"):
            self.ids.edit_message.text = "Please log in again."
            return

        try:
            quantity = int(self.ids.quantity.text)

            if quantity < 1:
                raise ValueError

        except ValueError:
            self.ids.edit_message.text = (
                "Quantity must be a whole number greater than zero."
            )
            return

        result = update_card_details(
            self.card,
            user["owner_id"],
            self.ids.condition.text,
            self.ids.foil.text == "Yes",
            quantity
        )

        self.ids.edit_message.text = result["message"]

        if result["success"]:
            inventory_screen = self.manager.get_screen("inventory")
            inventory_screen.refresh_inventory()

            self.manager.current = "inventory"
     
class VendorScreen(Screen):

    def show_my_listings(self):
        app = App.get_running_app()
        user = app.current_user

        if not user or not user.get("owner_id"):
            self.ids.vendor_message.text = "Please log in again."
            return

        owner_id = user["owner_id"]

        try:
            listings = list(
                vendor_booth.booth_collection.find(
                    {"owner_id": owner_id}
                ).sort("created_at", -1)
            )

            content = BoxLayout(
                orientation="vertical",
                spacing=10,
                padding=12
            )

            title = Label(
                text="MY VENDOR LISTINGS",
                font_size="20sp",
                size_hint_y=None,
                height=45
            )
            content.add_widget(title)

            scroll = ScrollView(
                do_scroll_x=False
            )

            listings_grid = GridLayout(
                cols=1,
                spacing=12,
                padding=5,
                size_hint_y=None
            )
            listings_grid.bind(
                minimum_height=listings_grid.setter("height")
            )

            if not listings:
                listings_grid.add_widget(
                    Label(
                        text="You have no vendor listings yet.",
                        size_hint_y=None,
                        height=60
                    )
                )

            else:
                for listing in listings:
                    card_text = (
                        f"{listing.get('card_name', 'Unknown card')}\n"
                        f"Set: {listing.get('set_code', '')} / "
                        f"{listing.get('collector_number', '')}\n"
                        f"Condition: {listing.get('condition', 'NM')} | "
                        f"Foil: {'Yes' if listing.get('foil', False) else 'No'}\n"
                        f"Quantity: {listing.get('quantity_listed', 0)}\n"
                        f"Type: {listing.get('listing_type', 'sale')}\n"
                        f"Price: {listing.get('price', 'Trade only')} "
                        f"{listing.get('currency', 'NZD')}\n"
                        f"Region: {listing.get('region', 'Not specified')}\n"
                        f"Status: {listing.get('status', 'unknown')}"
                    )

                    listing_row = ListingRow(
                        orientation="horizontal",
                        size_hint_y=None,
                        height=200,
                        padding=15,
                        spacing=10,
                    )

                    # Left side: the card details.
                    card_label = Label(
                        text=card_text,
                        halign="left",
                        valign="middle",
                    )
                    card_label.bind(
                        size=lambda instance, value: setattr(
                            instance, "text_size", value
                        )
                    )

                    listing_row.add_widget(card_label)
                    listings_grid.add_widget(listing_row)

            scroll.add_widget(listings_grid)
            content.add_widget(scroll)

            close_button = Button(
                text="CLOSE",
                size_hint_y=None,
                height=50
            )
            content.add_widget(close_button)

            self.listings_popup = Popup(
                title="",
                content=content,
                size_hint=(0.9, 0.85),
                auto_dismiss=False
            )

            close_button.bind(
                on_release=self.listings_popup.dismiss
            )

            self.listings_popup.open()

        except Exception as error:
            print("Vendor listings error:", error)
            self.ids.vendor_message.text = (
                "Could not load your listings."
            )
    

    def open_browse_marketplace(self):
        app = App.get_running_app()
        user = app.current_user

        if not user or not user.get("owner_id"):
            self.ids.vendor_message.text = "Please log in again."
            return

        owner_id = user["owner_id"]
        print("\nDEBUG MARKETPLACE ACCOUNT")
        print("Logged-in username:", user.get("username"))
        print("Logged-in owner_id:", repr(owner_id))

        try:
            listings = list(
                vendor_booth.booth_collection.find({
                    "status": "active",
                    "owner_id": {"$ne": owner_id}
                }).sort("created_at", -1)
            )
            
            print("\nDEBUG MARKETPLACE LISTINGS")
            for item in listings:
                print(
                    item.get("card_name"),
                    "Owner:",
                    repr(item.get("owner_id")),
                    "Same owner:",
                    item.get("owner_id") == owner_id
                )

            self.marketplace_listings = listings

            content = BoxLayout(
                orientation="vertical",
                spacing=10,
                padding=12
            )

            region_options = [
                "All Regions",
                "Northland",
                "Auckland",
                "Waikato",
                "Bay of Plenty",
                "Gisborne",
                "Hawke's Bay",
                "Taranaki",
                "Manawatu-Whanganui",
                "Wellington",
                "Tasman",
                "Nelson",
                "Marlborough",
                "West Coast",
                "Canterbury",
                "Otago",
                "Southland",
                "Chatham Islands",
                "Other / Outside New Zealand"
            ]

            region_label = Label(
                text="FILTER BY REGION",
                size_hint_y=None,
                height=30
            )
            content.add_widget(region_label)

            region_spinner = Spinner(
                text="All Regions",
                values=region_options,
                size_hint_y=None,
                height=50
            )
            content.add_widget(region_spinner)

            scroll = ScrollView(do_scroll_x=False)

            listings_grid = GridLayout(
                cols=3,
                spacing=12,
                padding=5,
                size_hint_y=None
            )
            listings_grid.bind(
                minimum_height=listings_grid.setter("height")
            )

            def refresh_marketplace(instance, selected_region):
                listings_grid.clear_widgets()

                if selected_region == "All Regions":
                    filtered_listings = listings
                else:
                    filtered_listings = [
                        listing for listing in listings
                        if listing.get("region") == selected_region
                    ]

                if not filtered_listings:
                    listings_grid.add_widget(
                        Label(
                            text="No active listings found in this region.",
                            size_hint_y=None,
                            height=60
                        )
                    )
                    return

                for listing in filtered_listings:
                    price = listing.get("price")

                    if price is None:
                        price_text = "Trade only"
                    else:
                        price_text = (
                            f"{price} {listing.get('currency', 'NZD')}"
                        )

                    card_text = (
                        f"{listing.get('card_name', 'Unknown card')}\n"
                        f"Set: {listing.get('set_code', '').upper()} / "
                        f"{listing.get('collector_number', '')}\n"
                        f"Condition: {listing.get('condition', 'NM')} | "
                        f"Foil: {'Yes' if listing.get('foil', False) else 'No'}\n"
                        f"Quantity: {listing.get('quantity_listed', 0)}\n"
                        f"Type: {listing.get('listing_type', 'sale')}\n"
                        f"Price: {price_text}\n"
                        f"Region: {listing.get('region', 'Not specified')}"
                    )

                    listing_row = ListingRow(
                        orientation="horizontal",
                        size_hint_y=None,
                        height=200,
                        padding=15,
                        spacing=10,
                    )

                    # Left side: the card details.
                    card_label = Label(
                        text=card_text,
                        size_hint_x=0.7,
                        halign="left",
                        valign="middle",
                    )
                    card_label.bind(
                        size=lambda instance, value: setattr(
                            instance, "text_size", value
                        )
                    )

                    # Right side: the call to action.
                    tap_label = Label(
                        text="TAP TO\nVIEW DETAILS",
                        size_hint_x=0.3,
                        halign="right",
                        valign="middle",
                        bold=True,
                    )
                    tap_label.bind(
                        size=lambda instance, value: setattr(
                            instance, "text_size", value
                        )
                    )

                    listing_row.add_widget(card_label)
                    listing_row.add_widget(tap_label)

                    listing_row.bind(
                        on_release=lambda instance, selected_listing=listing:
                            self.show_listing_details(selected_listing)
                    )

                    listings_grid.add_widget(listing_row)
                    
            region_spinner.bind(text=refresh_marketplace)

            refresh_marketplace(region_spinner, "All Regions")

            scroll.add_widget(listings_grid)
            content.add_widget(scroll)

            close_button = Button(
                text="CLOSE",
                size_hint_y=None,
                height=50
            )
            content.add_widget(close_button)

            self.marketplace_popup = Popup(
                title="MARKETPLACE LISTINGS",
                content=content,
                size_hint=(0.9, 0.85),
                auto_dismiss=False
            )

            close_button.bind(
                on_release=self.marketplace_popup.dismiss
            )

            self.marketplace_popup.open()

        except Exception as error:
            print("Marketplace browsing error:", error)
            self.ids.vendor_message.text = (
                "Could not load marketplace listings."
            )

    def show_listing_details(self, listing):
        try:
            content = BoxLayout(
                orientation="vertical",
                spacing=12,
                padding=15
            )

            price = listing.get("price")

            if price is None:
                price_text = "Trade only"
            else:
                price_text = (
                    f"{price} {listing.get('currency', 'NZD')}"
                )

            card_details = (
                f"[b]{listing.get('card_name', 'Unknown card')}[/b]\n\n"
                f"Set: {listing.get('set_code', '').upper()}\n"
                f"Collector Number: "
                f"{listing.get('collector_number', '')}\n\n"
                f"Condition: {listing.get('condition', 'NM')}\n"
                f"Foil: {'Yes' if listing.get('foil', False) else 'No'}\n"
                f"Available Quantity: "
                f"{listing.get('quantity_listed', 0)}\n\n"
                f"Listing Type: "
                f"{listing.get('listing_type', 'sale')}\n"
                f"Asking Price: {price_text}\n"
                f"Vendor Region: "
                f"{listing.get('region', 'Not specified')}"
            )

            details_label = Label(
                text=card_details,
                markup=True,
                size_hint_y=1,
                halign="middle",
                valign="middle"
            )

            details_label.bind(
                size=lambda instance, value: setattr(
                    instance, "text_size", value
                )
            )

            content.add_widget(details_label)

            enquiry_button = Button(
                text="MAKE AN ENQUIRY",
                size_hint_y=None,
                height=55
            )

            close_button = Button(
                text="CLOSE",
                size_hint_y=None,
                height=45
            )

            content.add_widget(enquiry_button)
            content.add_widget(close_button)

            self.listing_details_popup = Popup(
                title="LISTING DETAILS",
                content=content,
                size_hint=(0.9, 0.8),
                auto_dismiss=False
            )

            close_button.bind(
                on_release=self.listing_details_popup.dismiss
            )

            def make_enquiry(instance):
                self.listing_details_popup.dismiss()
                self.open_enquiry_popup(listing)

            enquiry_button.bind(on_release=make_enquiry)
            
            self.listing_details_popup.open()

        except Exception as error:
            print("Listing details error:", error)
            self.ids.vendor_message.text = (
                "Could not display listing details."
            )

    def open_enquiry_popup(self, listing):
        app = App.get_running_app()
        user = app.current_user

        if not user or not user.get("owner_id"):
            self.ids.vendor_message.text = "Please log in again."
            return

        buyer_owner_id = user["owner_id"]

        listing_type = listing.get("listing_type", "sale")

        enquiry_options = []

        if listing_type in ("sale", "sale_and_trade"):
            enquiry_options.append("purchase")

        if listing_type in ("trade", "sale_and_trade"):
            enquiry_options.append("trade")

        if not enquiry_options:
            self.ids.vendor_message.text = (
                "This listing does not accept enquiries."
            )
            return

        content = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=15
        )

        content.add_widget(Label(
            text=f"Enquire about: {listing.get('card_name', 'Unknown')}",
            size_hint_y=None,
            height=40
        ))

        content.add_widget(Label(
            text="Enquiry type",
            size_hint_y=None,
            height=25
        ))

        enquiry_spinner = Spinner(
            text=enquiry_options[0],
            values=enquiry_options,
            size_hint_y=None,
            height=45
        )
        content.add_widget(enquiry_spinner)

        content.add_widget(Label(
            text=f"Quantity (1-{listing.get('quantity_listed', 1)})",
            size_hint_y=None,
            height=25
        ))

        quantity_input = TextInput(
            text="1",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=45
        )
        content.add_widget(quantity_input)

        content.add_widget(Label(
            text="Your display name",
            size_hint_y=None,
            height=25
        ))

        name_input = TextInput(
            multiline=False,
            size_hint_y=None,
            height=45
        )
        content.add_widget(name_input)

        content.add_widget(Label(
            text="Your contact details",
            size_hint_y=None,
            height=25
        ))

        contact_input = TextInput(
            multiline=False,
            size_hint_y=None,
            height=45
        )
        content.add_widget(contact_input)

        content.add_widget(Label(
            text="Message / cards offered (required for trades)",
            size_hint_y=None,
            height=35
        ))

        message_input = TextInput(
            multiline=True,
            size_hint_y=1
        )
        content.add_widget(message_input)

        buttons = BoxLayout(
            size_hint_y=None,
            height=50,
            spacing=10
        )

        submit_button = Button(text="SUBMIT ENQUIRY")
        cancel_button = Button(text="CANCEL")

        buttons.add_widget(submit_button)
        buttons.add_widget(cancel_button)
        content.add_widget(buttons)

        enquiry_popup = Popup(
            title="Marketplace Enquiry",
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=False
        )

        def submit_enquiry(instance):
            result = vendor_booth.create_marketplace_enquiry(
                listing_id=listing["_id"],
                buyer_owner_id=buyer_owner_id,
                enquiry_type=enquiry_spinner.text,
                quantity=quantity_input.text,
                display_name=name_input.text,
                contact=contact_input.text,
                message=message_input.text
            )

            if result.get("success"):
                enquiry_popup.dismiss()

                self.ids.vendor_message.text = (
                    "Enquiry submitted successfully!"
                )

                confirmation = Popup(
                    title="Enquiry Submitted",
                    content=Label(
                        text=result.get("message", "Success!")
                    ),
                    size_hint=(0.8, 0.3)
                )
                confirmation.open()

            else:
                self.ids.vendor_message.text = result.get(
                    "error",
                    "Could not submit enquiry."
                )

        submit_button.bind(on_release=submit_enquiry)
        cancel_button.bind(on_release=enquiry_popup.dismiss)

        enquiry_popup.open()

    def show_my_enquiries(self):
        app = App.get_running_app()
        user = app.current_user

        if not user or not user.get("owner_id"):
            self.ids.vendor_message.text = "Please log in again."
            return

        owner_id = user["owner_id"]

        try:
            enquiries = vendor_booth.get_marketplace_enquiries(
                owner_id
            )

            content = BoxLayout(
                orientation="vertical",
                spacing=10,
                padding=12,
                size_hint_y=1,
                size_hint_x=1
            )

            scroll = ScrollView(
                do_scroll_x=False
            )

            enquiry_list = GridLayout(
                cols=2,
                spacing=10,
                size_hint_y=None
            )
            enquiry_list.bind(
                minimum_height=enquiry_list.setter("height")
            )

            if not enquiries:
                enquiry_list.add_widget(Label(
                    text="You have no marketplace enquiries.",
                    size_hint_y=None,
                    padding=[10, 20, 10, 10],  # Adds 20px top padding to the scroll area
                    height=60
                ))

            for enquiry in enquiries:
                card = BoxLayout(
                    orientation="vertical",
                    spacing=6,
                    padding=[10, 15, 10, 10],  # [left, top, right, bottom]
                    size_hint_y=None,
                    height=240
                )
                card.bind(minimum_height=card.setter("height"))

                card.add_widget(Label(
                    text=(
                        f"{enquiry.get('card_name', 'Unknown')} "
                        f"| {enquiry.get('enquiry_type', 'Unknown').upper()}"
                    ),
                    size_hint_y=None,
                    height=35
                ))

                card.add_widget(Label(
                    text=(
                        f"Quantity: "
                        f"{enquiry.get('quantity_requested', 0)}"
                    ),
                    size_hint_y=None,
                    height=25
                ))

                card.add_widget(Label(
                    text=(
                        f"From: {enquiry.get('display_name', 'Unknown')}"
                        f" | Contact: {enquiry.get('contact', 'Not provided')}"
                    ),
                    size_hint_y=None,
                    height=40
                ))

                card.add_widget(Label(
                    text=(
                        f"Message: {enquiry.get('message', '')}"
                    ),
                    size_hint_y=None,
                    height=45
                ))

                status = enquiry.get("status", "unknown").upper()

                card.add_widget(Label(
                    text=f"STATUS: {status}",
                    size_hint_y=None,
                    height=30
                ))

                if enquiry.get("status") == "pending":
                    actions = BoxLayout(
                        size_hint_y=None,
                        height=45,
                        spacing=10
                    )

                    accept_button = Button(text="ACCEPT")
                    decline_button = Button(text="DECLINE")

                    actions.add_widget(accept_button)
                    actions.add_widget(decline_button)

                    def update_status(
                        new_status,
                        selected_enquiry=enquiry
                    ):
                        success = (
                            vendor_booth.update_marketplace_enquiry_status(
                                selected_enquiry["_id"],
                                owner_id,
                                new_status
                            )
                        )

                        if success:
                            popup.dismiss()
                            self.show_my_enquiries()
                            self.ids.vendor_message.text = (
                                f"Enquiry {new_status} successfully."
                            )
                        else:
                            self.ids.vendor_message.text = (
                                "Could not update enquiry. "
                                "It may already have changed."
                            )

                    accept_button.bind(
                        on_release=lambda instance:
                            update_status("accepted")
                    )

                    decline_button.bind(
                        on_release=lambda instance:
                            update_status("declined")
                    )

                    card.add_widget(actions)

                enquiry_list.add_widget(card)

            scroll.add_widget(enquiry_list)
            content.add_widget(scroll)

            close_button = Button(
                text="CLOSE",
                size_hint_y=None,
                height=45
            )
            content.add_widget(close_button)

            popup = Popup(
                title="MY MARKETPLACE ENQUIRIES",
                content=content,
                size_hint=(0.95, 0.9),
                auto_dismiss=False
            )

            close_button.bind(
                on_release=popup.dismiss
            )

            popup.open()

        except Exception as error:
            print("Marketplace enquiry inbox error:", error)
            self.ids.vendor_message.text = (
                "Could not load marketplace enquiries."
            )

    def open_create_listing(self):
        app = App.get_running_app()
        user = app.current_user

        if not user or not user.get("owner_id"):
            self.ids.vendor_message.text = "Please log in again."
            return

        owner_id = user["owner_id"]

        try:
            cards = list(
                vendor_booth.inventory_collection.find(
                    {"owner_id": owner_id}
                ).sort("name", 1)
            )

            self.available_listing_cards = {}

            for card in cards:
                available = vendor_booth.get_available_quantity(
                    card, owner_id
                )

                if available > 0:
                    condition = card.get("condition", "NM")
                    foil = "Foil" if card.get("foil", False) else "Non-foil"

                    display_name = (
                        f"{card.get('name', 'Unknown')} | "
                        f"{card.get('set', '').upper()}/"
                        f"{card.get('collector_number', '')} | "
                        f"{condition} | {foil} | "
                        f"Available: {available} | "
                        
                    )

                    self.available_listing_cards[display_name] = card
                    
            if not self.available_listing_cards:
                self.ids.vendor_message.text = (
                    "No inventory copies available to list."
                )
                return

            content = BoxLayout(
                orientation="vertical",
                padding=15,
                spacing=10
            )

            content.add_widget(Label(
                text="CREATE VENDOR LISTING",
                size_hint_y=None,
                height=40
            ))

            self.listing_card_spinner = Spinner(
                text="Select a card",
                values=list(self.available_listing_cards.keys()),
                size_hint_y=None,
                height=45
            )
            content.add_widget(self.listing_card_spinner)

            self.listing_quantity = TextInput(
                hint_text="Quantity to list",
                multiline=False,
                input_filter="int",
                size_hint_y=None,
                height=45
            )
            content.add_widget(self.listing_quantity)

            self.listing_type_spinner = Spinner(
                text="sale",
                values=("sale", "trade", "sale_and_trade"),
                size_hint_y=None,
                height=45
            )
            content.add_widget(self.listing_type_spinner)

            self.listing_price = TextInput(
                hint_text="Asking price per copy (NZD)",
                multiline=False,
                input_filter="float",
                size_hint_y=None,
                height=45
            )
            content.add_widget(self.listing_price)

            self.listing_trade_options = TextInput(
                hint_text="Wanted cards (comma-separated)",
                multiline=False,
                size_hint_y=None,
                height=45
            )
            content.add_widget(self.listing_trade_options)

            self.listing_region = Spinner(
                text="Select your region",
                values=(
                    "Northland",
                    "Auckland",
                    "Waikato",
                    "Bay of Plenty",
                    "Gisborne",
                    "Hawke's Bay",
                    "Taranaki",
                    "Manawatu-Whanganui",
                    "Wellington",
                    "Tasman",
                    "Nelson",
                    "Marlborough",
                    "West Coast",
                    "Canterbury",
                    "Otago",
                    "Southland",
                    "Chatham Islands",
                    "Other / Outside New Zealand"
                ),
                size_hint_y=None,
                height=45
            )
            content.add_widget(self.listing_region)

            self.listing_popup_message = Label(
                text="",
                size_hint_y=None,
                height=40
            )
            content.add_widget(self.listing_popup_message)

            create_button = Button(
                text="CREATE LISTING",
                size_hint_y=None,
                height=50
            )
            create_button.bind(
                on_release=self.submit_listing
            )
            content.add_widget(create_button)

            close_button = Button(
                text="CANCEL",
                size_hint_y=None,
                height=45
            )
            content.add_widget(close_button)

            self.create_listing_popup = Popup(
                title="Vendor Listing",
                content=content,
                size_hint=(0.9, 0.9),
                auto_dismiss=False
            )

            close_button.bind(
                on_release=self.create_listing_popup.dismiss
            )

            self.create_listing_popup.open()

        except Exception as error:
            print("Create listing popup error:", error)
            self.ids.vendor_message.text = (
                "Could not open the listing form."
            )
            
    def submit_listing(self, instance):
        selected_card = self.listing_card_spinner.text

        if selected_card not in self.available_listing_cards:
            self.listing_popup_message.text = "Please select a card."
            return

        quantity_text = self.listing_quantity.text.strip()
        region = self.listing_region.text.strip()
        listing_type = self.listing_type_spinner.text

        if not quantity_text or region == "Select your region":
            self.listing_popup_message.text = (
                "Please enter a quantity and region."
            )
            return

        try:
            quantity = int(quantity_text)

            if quantity < 1:
                raise ValueError

        except ValueError:
            self.listing_popup_message.text = (
                "Quantity must be at least 1."
            )
            return

        price = None

        if listing_type in ("sale", "sale_and_trade"):
            price = self.listing_price.text.strip()

            if not price:
                self.listing_popup_message.text = (
                    "Please enter an asking price."
                )
                return

            try:
                price = float(price)

                if price < 0:
                    raise ValueError

            except ValueError:
                self.listing_popup_message.text = (
                    "Enter a valid non-negative price."
                )
                return

        trade_options = []

        if listing_type in ("trade", "sale_and_trade"):
            trade_options = [
                item.strip()
                for item in self.listing_trade_options.text.split(",")
                if item.strip()
            ]

            if not trade_options:
                self.listing_popup_message.text = (
                    "Please enter cards you would accept in trade."
                )
                return

        app = App.get_running_app()
        owner_id = app.current_user["owner_id"]
        card = self.available_listing_cards[selected_card]

        try:
            success = vendor_booth.create_listing(
                owner_id=owner_id,
                inventory_id=card["_id"],
                quantity_listed=quantity,
                listing_type=listing_type,
                region=region,
                price=price,
                currency="NZD",
                trade_options=trade_options
            )

            if success:
                self.create_listing_popup.dismiss()
                self.ids.vendor_message.text = (
                    "Vendor listing created successfully!"
                )
                self.show_my_listings()
            else:
                self.listing_popup_message.text = (
                    "Listing could not be created. "
                    "Check the quantity and listing details."
                )

        except Exception as error:
            print("Listing submission error:", error)
            self.listing_popup_message.text = (
                "An error occurred while creating the listing."
            )
       
class TheRoundTableApp(App):

    current_user = None

    def build(self):
        self.title = "The Round Table"
        return Builder.load_string(KV)


if __name__ == "__main__":
    TheRoundTableApp().run()
