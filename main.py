import random
import sys
import time
import hahmot
import kartta
import taistelu

ALLOWED_ISO = {
    "AD", "AL", "AT", "BE", "BG", "BA", "BY", "CY", "HR", "CZ",
    "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IS", "IT",
    "LV", "LI", "LT", "LU", "MT", "MD", "ME", "MK", "NL", "NO",
    "PL", "PT", "RO", "RS", "SK", "SI", "ES", "SE", "CH", "TR",
    "UA", "GB", "SM", "MC", "VA",
}

def color(text, code):
    return f"\033[{code}m{text}\033[0m"


def slow_print(text, delay=0.05):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def print_story():
    story = [
        "🤖 Robotit ovat vallanneet maapallon!",
        "💥 Niiden mielestä ihmiskunta on liian vaarallinen elämään…",
        "🌍 Seitsemän päivän kuluttua ne aikovat räjäyttää koko planeetan.",
        "🚀 Ainoa toivo on rakentaa raketti ja paeta Kuuhun.",
        "🛩️ Sinun täytyy matkustaa lentokentältä toiselle ympäri Eurooppaa,",
        "   kerätä puuttuvat raketin osat sekä polttoaine ja tarvikkeet.",
        "🔧 Jokainen osa on piilotettu eri maahan – etsi ne!",
        "🌝 Vasta kun kaikki osat on löydetty ja raketti on rakennettu,",
        "   voit paeta Kuuhun ennen kuin Maapallo katoaa ikuisiksi ajoiksi.",
        "💪 Onnistutko pelastamaan ihmiskunnan?",
    ]
    for line in story:
        slow_print(color(line, "36"), 0.03)
        time.sleep(0.5)


def airplane_to_globe(dest_country):
    plane = "✈"
    globe = "🌍"
    smoke = "💨"
    width = 12
    for i in range(width + 1):
        sys.stdout.write("\r")
        if i > 0:
            line = " " * (i - 1) + smoke + plane
        else:
            line = " " * i + plane
        line += " " * (width - i) + globe
        sys.stdout.write(line)
        sys.stdout.flush()
        time.sleep(0.2)
    slow_print("\n✈ Saavuit maahan " + dest_country + "! 🛬", 0.03)


def display_status(state, player, conn):
    loc = state["location"]
    loc_name = kartta.get_country_name(conn, loc["iso_country"])
    print("\n" + color("=" * 60, "36"))
    print(color("Sijainti: " + loc_name + " (" + loc["iso_country"] + ")", "34"))
    print(color("Aikaa jäljellä: " + str(state["time_left"]) + " h  |  Kantama: " + str(state["range_km"]) + " km", "34"))
    print(color("❤️ HP: " + str(player["hp"]) + "/100", "35"))
    print(color("Inventaario:", "34"))
    inv_line = "  🍎 Ruoka: " + str(player["ruoka"]) + "    ⛽ Fuel: " + str(player["fuel"]) + "    🔫 Ammo: " + str(player["ammo"]) + "    🚀 Osat: " + str(player["rakettiosat"])
    print(color(inv_line, "34"))
    if state["parts"]:
        print(color("Rakettiosat vielä maissa:", "34"))
        for iso in state["parts"]:
            cname = kartta.get_country_name(conn, iso)
            print(color("  * " + cname + " (" + iso + ")", "33"))
    else:
        print(color("Kaikki rakettiosat on kerätty!", "32"))


def choose_role():
    print(color("\nValitse hahmosi:", "36"))
    print(color(" [1] 🍳 Kokki – enemmän ruokaa", "36"))
    print(color(" [2] ✈️  Pilotti – enemmän polttoainetta", "36"))
    print(color(" [3] 🛡️ Taistelija – enemmän ammuksia", "36"))
    while True:
        c = input("> ").strip()
        if c == "1":
            return "kokki"
        if c == "2":
            return "pilotti"
        if c == "3":
            return "taistelija"
        print("Virheellinen valinta. Yritä uudelleen.")


def enemy_encounter(player):
    slow_print(color("\n👾 Matkan jälkeen kohtaat vihollisen!", "35"), 0.03)
    if player["ammo"] > 0:
        player["ammo"] -= 1
        slow_print(color("💥 Käytät yhden ammuksen ja voitat vihollisen!", "32"), 0.03)
        loot = hahmot.generate_loot()
        hahmot.add_loot(player, loot)
        gained_items = []
        for k in loot:
            if loot[k] > 0:
                gained_items.append(k + "+" + str(loot[k]))
        if gained_items:
            slow_print(color("🎁 Saat taistelusta lootin: " + ", ".join(gained_items) + ".", "32"), 0.03)
        if player["ammo"] == 0:
            player["ammo"] += 1
            slow_print(color("💫 Sait yhden hätäammuksen taistelusta!", "32"), 0.03)
        return True
    else:
        slow_print(color("💀 Sinulla ei ole ammuksia! Hävisit taistelun ja peli päättyy.", "31"), 0.03)
        return False


def boss_fight(player):
    slow_print(color("\n👹 Bossfight alkaa!", "35"), 0.03)
    if player["ammo"] > 0:
        player["ammo"] -= 1
        slow_print(color("🔥 Ammuit bossin ja voitit! Raketti rakennetaan ja lennät Kuuhun!", "32"), 0.03)
        return True
    else:
        slow_print(color("😭 Ei ammuksia bossiin, hävisit bossille.", "31"), 0.03)
        return False


def main():
    print(color("=" * 60, "36"))
    print(color(" LAST FLIGHT ".center(60, "="), "35"))
    print(color("Tavoite: Kerää 4 rakettiosaa ja palaa Suomeen pakoon Kuuhun.", "36"))
    print(color("=" * 60, "36"))
    print_story()
    conn = kartta.get_connection()
    rooli = choose_role()
    player = hahmot.create_player(rooli)
    player["hp"] = 100
    start_info = kartta.get_airport_by_icao(conn, "EFHK")
    state = {
        "location": start_info,
        "range_km": 400,
        "time_left": 168,
        "parts": random.sample([iso for iso in ALLOWED_ISO if iso != "FI"], 4),
    }
    fuel_cost = 30
    while True:
        if state["time_left"] <= 0:
            print(color("Aika loppui! Et ehtinyt kerätä kaikkia osia.", "31"))
            break
        if player["fuel"] < fuel_cost:
            print(color("Polttoaine loppui! Et voi enää lentää.", "31"))
            break
        if player["hp"] <= 0:
            print(color("HP loppui! Kuolit seikkailussa.", "31"))
            break
        display_status(state, player, conn)
        if not state["parts"] and state["location"]["iso_country"] == "FI":
            if boss_fight(player):
                print(color("Onneksi olkoon, peli läpäisty!", "32"))
            else:
                print(color("Peli päättyi tappioon.", "31"))
            break
        if not state["parts"] and state["location"]["iso_country"] != "FI":
            print(color("\nSinulla on kaikki rakettiosat! Palaa Suomeen (Finland) rakentamaan raketti.", "35"))
        print(color("\nMitä haluat tehdä?", "36"))
        print(color(" [l] ✈ Lennot (näytä kohteet)", "36"))
        print(color(" [i] 🎒 Inventaario", "36"))
        print(color(" [q] ❌ Lopeta peli", "36"))
        action = input("> ").strip().lower()
        if action == "q":
            print(color("Lopetit pelin.", "31"))
            break
        elif action == "i":
            print(color("\n--- Inventaario ---", "36"))
            print(color("🍎 Ruoka: " + str(player["ruoka"]), "34"))
            print(color("⛽ Fuel: " + str(player["fuel"]), "34"))
            print(color("🔫 Ammo: " + str(player["ammo"]), "34"))
            print(color("🚀 Osat: " + str(player["rakettiosat"]), "34"))
            print(color("❤️ HP: " + str(player["hp"]) + "/100", "34"))
            if player["ruoka"] > 0:
                print(color("\nSyö ruoka palauttaaksesi HP:tä (+10), tai paina Enter ohittaaksesi.", "36"))
                c = input("> ").strip().lower()
                if c in ("h", "1"):
                    player["ruoka"] -= 1
                    if player["hp"] >= 100:
                        print(color("HP on jo täynnä, et voi lisätä enempää.", "33"))
                        player["ruoka"] += 1
                    else:
                        player["hp"] = min(100, player["hp"] + 10)
                        print(color("Söit ruoan ja palautit 10 HP:tä.", "32"))
            else:
                print(color("Sinulla ei ole ruokaa käytettäväksi.", "33"))
            continue
        elif action == "l":
            options_raw = kartta.nearest_country_options(conn, state["location"], state["range_km"])
            options = []
            for opt in options_raw:
                dest_info = kartta.get_airport_by_icao(conn, opt["icao"])
                iso = dest_info["iso_country"]
                if iso in ALLOWED_ISO and iso != state["location"]["iso_country"]:
                    options.append({
                        "country": kartta.get_country_name(conn, iso),
                        "icao": opt["icao"],
                        "iso": iso,
                        "distance": opt["distance"],
                    })
            if not options:
                print(color("Ei ole maita kantaman sisällä! Hanki lisää rangea tai polttoainetta.", "33"))
                continue
            print(color("\nMahdolliset kohteet:", "36"))
            idx_num = 1
            for opt in options:
                mark = ""
                if opt["iso"] in state["parts"]:
                    mark = " [R]"
                home_mark = ""
                if opt["iso"] == "FI":
                    home_mark = " [koti]"
                line = " " + str(idx_num) + ". ✈ " + opt["country"] + " (" + format(opt["distance"], ".1f") + " km)" + mark + home_mark
                print(color(line, "36"))
                idx_num += 1
            print(color("\nSyötä kohteen numero lentääksesi tai paina Enter peruuttaaksesi.", "36"))
            sel = input("> ").strip()
            if sel == "":
                continue
            try:
                idx = int(sel) - 1
                if idx < 0 or idx >= len(options):
                    raise ValueError
            except ValueError:
                print(color("Virheellinen valinta. Yritä uudelleen.", "33"))
                continue
            dest = options[idx]
            if player["fuel"] < fuel_cost:
                print(color("Ei tarpeeksi polttoainetta lennolle!", "33"))
                continue
            print(color("\nLento käynnistyy...", "36"))
            airplane_to_globe(dest["country"])
            player["fuel"] -= fuel_cost
            state["time_left"] -= 12
            state["range_km"] += 50
            player["hp"] -= 10
            new_loc = kartta.get_airport_by_icao(conn, dest["icao"])
            state["location"] = new_loc
            slow_print(color("Lensit maahan " + dest["country"] + ". Aika -12h, Fuel -" + str(fuel_cost) + ", Range +50, HP -10.", "35"), 0.03)
            time.sleep(0.3)
            if dest["iso"] in state["parts"]:
                hahmot.add_rocket_part(player, 1)
                state["parts"].remove(dest["iso"])
                slow_print(color("Löysit rakettiosan maasta " + dest["country"] + "!", "32"), 0.03)
                time.sleep(0.3)
            loot = hahmot.generate_loot()
            hahmot.add_loot(player, loot)
            gained = []
            for k, v in loot.items():
                if v > 0:
                    gained.append(k + "+" + str(v))
            if gained:
                slow_print(color("Sait lootin: " + ", ".join(gained) + ".", "32"), 0.03)
                time.sleep(0.3)
            if taistelu.encounter_chance():
                if not enemy_encounter(player):
                    break
            input(color("\nPaina Enter jatkaaksesi seuraavaan vaiheeseen…", "36"))
            continue
        else:
            print(color("Tuntematon valinta. Käytä 'l', 'i' tai 'q'.", "33"))
            continue
    return


if __name__ == "__main__":
    main()