CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    year INTEGER NOT NULL,
    genre VARCHAR(50) NOT NULL,
    rating NUMERIC(3,1) NOT NULL,
    director VARCHAR(150),
    description TEXT
);

INSERT INTO movies (title, year, genre, rating, director, description) VALUES
('Neon Horizon', 2019, 'Sci-Fi', 8.7, 'Ava Kessler', 'A salvage pilot discovers a signal that predates humanity, hidden in the rings of a dead planet.'),
('The Quiet Ledger', 2021, 'Drama', 8.2, 'Marcus Oduya', 'An accountant uncovers a fraud that ties her own family to a decades-old cover-up.'),
('Rustwater', 2018, 'Thriller', 7.9, 'Ingrid Solheim', 'A drought-stricken town turns on itself when the last well runs dry.'),
('Paper Kingdoms', 2022, 'Animation', 8.5, 'Haruto Ishida', 'A origami-folder discovers her creations come alive after midnight.'),
('Iron Choir', 2017, 'Action', 7.6, 'Dominic Reyes', 'A disbanded military unit reunites to stop a weapons deal that could restart a war.'),
('Salt and Static', 2020, 'Horror', 7.3, 'Petra Vance', 'A lighthouse keeper starts hearing voices in the radio static during a storm.'),
('Midnight Ferry', 2016, 'Mystery', 8.0, 'Lucia Fernandez', 'Passengers on a night ferry realize one of them is not who they claim to be.'),
('The Cartographer', 2023, 'Adventure', 8.9, 'Nils Bergstrom', 'A mapmaker sets out to chart the last unexplored valley on Earth.'),
('Glass Orchard', 2015, 'Romance', 7.4, 'Simone Laurent', 'Two rival winemakers fall in love while fighting over the same plot of land.'),
('Static Revolution', 2024, 'Sci-Fi', 8.3, 'Kwame Asante', 'An AI gains sentience inside a city-wide power grid and must decide humanity''s fate.'),
('The Long Recess', 2019, 'Comedy', 7.1, 'Danny Whitfield', 'A substitute teacher accidentally becomes the most beloved figure in a small town.'),
('Hollow Pines', 2021, 'Horror', 7.8, 'Petra Vance', 'A family inherits a cabin where the trees seem to remember what happened there.'),
('Border of Ash', 2018, 'War', 8.6, 'Rasha Aziz', 'Two soldiers on opposite sides share a single night of ceasefire before the final battle.'),
('The Understudy', 2020, 'Drama', 7.7, 'Marcus Oduya', 'A backup actor gets one chance at the stage and cannot decide if he wants it.'),
('Copper Season', 2022, 'Drama', 8.1, 'Ingrid Solheim', 'A mining town faces its final harvest before the company shuts the pits for good.'),
('Vantablack', 2023, 'Thriller', 8.4, 'Ava Kessler', 'A heist crew targets an art installation made from the darkest material on Earth.'),
('Echoes of Marrakech', 2017, 'Romance', 7.5, 'Simone Laurent', 'A photographer and a spice trader cross paths during a citywide festival.'),
('The Last Cartridge', 2016, 'Action', 7.2, 'Dominic Reyes', 'A retired printer-repair technician becomes the unlikely hero of a small uprising.'),
('Driftwood Radio', 2019, 'Comedy', 7.9, 'Danny Whitfield', 'A failing coastal radio station gets a second life when a whale becomes their mascot.'),
('The Cold Choir', 2024, 'Mystery', 8.8, 'Lucia Fernandez', 'A choir director investigates the disappearance of her lead soprano during rehearsal week.');
