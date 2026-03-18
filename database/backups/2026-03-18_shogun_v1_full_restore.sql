--
-- PostgreSQL database dump
--

\restrict nEg41e7zdz4WQttDLXws43FHc1A9Ltzoxg8sKVbKzac76y1AZxLNf2UwBX4R6qV

-- Dumped from database version 17.9 (Debian 17.9-1.pgdg12+1)
-- Dumped by pg_dump version 17.9 (Debian 17.9-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.wishlist_items DROP CONSTRAINT IF EXISTS wishlist_items_reviewed_by_fkey;
ALTER TABLE IF EXISTS ONLY public.wishlist_items DROP CONSTRAINT IF EXISTS wishlist_items_requested_by_fkey;
ALTER TABLE IF EXISTS ONLY public.user_preferences DROP CONSTRAINT IF EXISTS user_preferences_user_id_fkey;
DROP INDEX IF EXISTS public.uidx_knowledge_items;
DROP INDEX IF EXISTS public.uidx_knowledge_anchor_cat_url;
DROP INDEX IF EXISTS public.idx_wishlist_status;
DROP INDEX IF EXISTS public.idx_wishlist_requested_by;
DROP INDEX IF EXISTS public.idx_user_pref_user_id;
DROP INDEX IF EXISTS public.idx_user_pref_category;
DROP INDEX IF EXISTS public.idx_pois_tags;
DROP INDEX IF EXISTS public.idx_pois_city;
DROP INDEX IF EXISTS public.idx_pois_category;
DROP INDEX IF EXISTS public.idx_knowledge_city;
DROP INDEX IF EXISTS public.idx_knowledge_category;
DROP INDEX IF EXISTS public.idx_itinerary_date;
DROP INDEX IF EXISTS public.idx_itinerary_city;
DROP INDEX IF EXISTS public.idx_checklist_packed;
DROP INDEX IF EXISTS public.idx_checklist_category;
ALTER TABLE IF EXISTS ONLY public.wishlist_items DROP CONSTRAINT IF EXISTS wishlist_items_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_telegram_user_id_key;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.user_preferences DROP CONSTRAINT IF EXISTS user_preferences_pkey;
ALTER TABLE IF EXISTS ONLY public.trip_pois DROP CONSTRAINT IF EXISTS trip_pois_pkey;
ALTER TABLE IF EXISTS ONLY public.trip_itinerary DROP CONSTRAINT IF EXISTS trip_itinerary_pkey;
ALTER TABLE IF EXISTS ONLY public.knowledge_items DROP CONSTRAINT IF EXISTS knowledge_items_pkey;
ALTER TABLE IF EXISTS ONLY public.checklist_items DROP CONSTRAINT IF EXISTS checklist_items_pkey;
ALTER TABLE IF EXISTS ONLY public.budget_items DROP CONSTRAINT IF EXISTS budget_items_pkey;
ALTER TABLE IF EXISTS public.wishlist_items ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.user_preferences ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.trip_pois ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.trip_itinerary ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.knowledge_items ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.checklist_items ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.budget_items ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.wishlist_items_id_seq;
DROP TABLE IF EXISTS public.wishlist_items;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP SEQUENCE IF EXISTS public.user_preferences_id_seq;
DROP TABLE IF EXISTS public.user_preferences;
DROP SEQUENCE IF EXISTS public.trip_pois_id_seq;
DROP TABLE IF EXISTS public.trip_pois;
DROP SEQUENCE IF EXISTS public.trip_itinerary_id_seq;
DROP TABLE IF EXISTS public.trip_itinerary;
DROP SEQUENCE IF EXISTS public.knowledge_items_id_seq;
DROP TABLE IF EXISTS public.knowledge_items;
DROP SEQUENCE IF EXISTS public.checklist_items_id_seq;
DROP TABLE IF EXISTS public.checklist_items;
DROP SEQUENCE IF EXISTS public.budget_items_id_seq;
DROP TABLE IF EXISTS public.budget_items;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: budget_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.budget_items (
    id integer NOT NULL,
    trip_date date,
    category character varying(30) DEFAULT 'other'::character varying NOT NULL,
    description text NOT NULL,
    amount_jpy integer NOT NULL,
    created_utc timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: budget_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.budget_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: budget_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.budget_items_id_seq OWNED BY public.budget_items.id;


--
-- Name: checklist_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.checklist_items (
    id integer NOT NULL,
    category text DEFAULT 'misc'::text NOT NULL,
    item_name text NOT NULL,
    packed boolean DEFAULT false NOT NULL,
    notes text,
    created_utc timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE checklist_items; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.checklist_items IS 'Trip packing checklist — items with packed/unpacked state';


--
-- Name: COLUMN checklist_items.category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.checklist_items.category IS 'Item category: documents, clothing, electronics, toiletries, misc';


--
-- Name: COLUMN checklist_items.packed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.checklist_items.packed IS 'True when item has been packed';


--
-- Name: checklist_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.checklist_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: checklist_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.checklist_items_id_seq OWNED BY public.checklist_items.id;


--
-- Name: knowledge_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.knowledge_items (
    id integer NOT NULL,
    anchor text,
    city text,
    category text,
    topic text,
    source_url text,
    content_summary text,
    raw_content text,
    tavily_score double precision,
    ingested_utc timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE knowledge_items; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.knowledge_items IS 'Trip knowledge base for AI RAG search — local tips, places, food';


--
-- Name: COLUMN knowledge_items.topic; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.knowledge_items.topic IS 'Short searchable title for this knowledge item';


--
-- Name: COLUMN knowledge_items.content_summary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.knowledge_items.content_summary IS 'AI-readable summary: 1-3 sentences of actionable knowledge';


--
-- Name: knowledge_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.knowledge_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: knowledge_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.knowledge_items_id_seq OWNED BY public.knowledge_items.id;


--
-- Name: trip_itinerary; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trip_itinerary (
    id integer NOT NULL,
    leg_sequence integer NOT NULL,
    leg_type text NOT NULL,
    date_local date NOT NULL,
    city text NOT NULL,
    title text NOT NULL,
    address_en text,
    address_ja text,
    contact_phone text,
    confirmation_number text,
    notes_en text,
    notes_ja text,
    start_time time without time zone,
    end_time time without time zone,
    created_utc timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT trip_itinerary_leg_type_check CHECK ((leg_type = ANY (ARRAY['flight'::text, 'accommodation'::text, 'activity'::text, 'transit'::text])))
);


--
-- Name: TABLE trip_itinerary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.trip_itinerary IS 'Full trip schedule: flights, accommodation, activities, transit';


--
-- Name: COLUMN trip_itinerary.leg_sequence; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trip_itinerary.leg_sequence IS 'Explicit ordering; not auto-derived from date (flights cross midnight)';


--
-- Name: COLUMN trip_itinerary.date_local; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trip_itinerary.date_local IS 'Local date at destination, not UTC';


--
-- Name: trip_itinerary_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.trip_itinerary_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: trip_itinerary_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.trip_itinerary_id_seq OWNED BY public.trip_itinerary.id;


--
-- Name: trip_pois; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trip_pois (
    id integer NOT NULL,
    city text NOT NULL,
    name_en text NOT NULL,
    name_ja text,
    category text NOT NULL,
    lat numeric(10,7),
    lng numeric(10,7),
    address_en text,
    address_ja text,
    tags text[] DEFAULT '{}'::text[] NOT NULL,
    crowd_notes text,
    best_time_notes text,
    source text,
    created_utc timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE trip_pois; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.trip_pois IS 'Points of interest by city with crowd intelligence and user-layer tags';


--
-- Name: COLUMN trip_pois.tags; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trip_pois.tags IS 'Array of searchable tags: ghibli, anime, knife, madeline, early-morning-only, etc.';


--
-- Name: COLUMN trip_pois.source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.trip_pois.source IS 'How this POI was ingested: manual, tavily, google_places';


--
-- Name: trip_pois_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.trip_pois_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: trip_pois_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.trip_pois_id_seq OWNED BY public.trip_pois.id;


--
-- Name: user_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_preferences (
    id integer NOT NULL,
    user_id integer NOT NULL,
    category text NOT NULL,
    preference_key text NOT NULL,
    preference_value text NOT NULL,
    notes text,
    created_utc timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT user_preferences_category_check CHECK ((category = ANY (ARRAY['dietary'::text, 'likes'::text, 'dislikes'::text, 'shopping'::text, 'entertainment'::text])))
);


--
-- Name: TABLE user_preferences; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.user_preferences IS 'Trip-long user preferences: dietary, shopping, entertainment';


--
-- Name: COLUMN user_preferences.preference_key; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_preferences.preference_key IS 'Preference dimension (e.g. eats, avoids, interest_type)';


--
-- Name: COLUMN user_preferences.notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_preferences.notes IS 'Freeform context from user questionnaire';


--
-- Name: user_preferences_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_preferences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_preferences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_preferences_id_seq OWNED BY public.user_preferences.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    telegram_user_id bigint NOT NULL,
    display_name text NOT NULL,
    full_name text,
    notification_active boolean DEFAULT true NOT NULL,
    language_preference text DEFAULT 'en'::text NOT NULL,
    created_utc timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.users IS 'Telegram users registered with Shogun';


--
-- Name: COLUMN users.telegram_user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.telegram_user_id IS 'Stable Telegram numeric user ID (from bot update payload)';


--
-- Name: COLUMN users.notification_active; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.notification_active IS 'If false, user receives no unsolicited location-triggered messages';


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: wishlist_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wishlist_items (
    id integer NOT NULL,
    requested_by integer NOT NULL,
    city text,
    description text NOT NULL,
    ai_research text,
    status text DEFAULT 'pending'::text NOT NULL,
    reviewed_by integer,
    reviewed_at timestamp with time zone,
    itinerary_note text,
    created_utc timestamp with time zone DEFAULT now() NOT NULL,
    category character varying(30) DEFAULT 'general'::character varying,
    needs_reservation boolean DEFAULT false NOT NULL,
    reservation_confirmed boolean DEFAULT false NOT NULL,
    CONSTRAINT wishlist_items_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text])))
);


--
-- Name: wishlist_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.wishlist_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: wishlist_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.wishlist_items_id_seq OWNED BY public.wishlist_items.id;


--
-- Name: budget_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_items ALTER COLUMN id SET DEFAULT nextval('public.budget_items_id_seq'::regclass);


--
-- Name: checklist_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_items ALTER COLUMN id SET DEFAULT nextval('public.checklist_items_id_seq'::regclass);


--
-- Name: knowledge_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_items ALTER COLUMN id SET DEFAULT nextval('public.knowledge_items_id_seq'::regclass);


--
-- Name: trip_itinerary id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_itinerary ALTER COLUMN id SET DEFAULT nextval('public.trip_itinerary_id_seq'::regclass);


--
-- Name: trip_pois id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_pois ALTER COLUMN id SET DEFAULT nextval('public.trip_pois_id_seq'::regclass);


--
-- Name: user_preferences id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_preferences ALTER COLUMN id SET DEFAULT nextval('public.user_preferences_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: wishlist_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wishlist_items ALTER COLUMN id SET DEFAULT nextval('public.wishlist_items_id_seq'::regclass);


--
-- Data for Name: budget_items; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: checklist_items; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.checklist_items (id, category, item_name, packed, notes, created_utc) VALUES
	(2, 'documents', 'Travel insurance docs', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(3, 'documents', 'JR Pass', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(4, 'documents', 'Hotel confirmations', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(5, 'documents', 'Yen cash', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(6, 'electronics', 'Phone charger', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(7, 'electronics', 'Power adapter (Type A)', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(8, 'electronics', 'Portable battery pack', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(9, 'electronics', 'Camera', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(10, 'clothing', 'Walking shoes', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(11, 'clothing', 'Rain jacket', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(12, 'toiletries', 'Medications', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(13, 'toiletries', 'Sunscreen', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(14, 'misc', 'Luggage locks', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(15, 'misc', 'Reusable bag', false, NULL, '2026-03-17 03:43:44.176309+00'),
	(1, 'documents', 'Passport', true, NULL, '2026-03-17 03:43:44.176309+00');


--
-- Data for Name: knowledge_items; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.knowledge_items (id, anchor, city, category, topic, source_url, content_summary, raw_content, tavily_score, ingested_utc) VALUES
	(579, NULL, 'tokyo', 'vintage', 'Shimokitazawa vintage clothing Tokyo best shops 2026', 'https://www.trip.com/moments/theme/poi-shimokitazawa-shopping-street-18687487-store-993139/', '### Shimokitazawa shopping street Address:. ### Shimokitazawa shopping street Opening times:. * ### Shimokitazawa Vintage Shop | Finding treasures requires patience and a discerning eye 👕. Shimokitazawa is Tokyo''s vintage clothing mecca; come here if you''re looking to find great deals. The area boasts dozens of vintage shops, each with a distinct style. 📍 Shimokitazawa 🚃 Odakyu Line/Keio Inokashira Shimokitazawa Station 💡 Each shop has a different style, it''s best to visit several. #JapanTravel #Tokyo #Shimokitazawa #Vintage #SecondhandClothing #TreasureHunting #Shopping #JapanTravel #JanuaryDestinations2026. From morning to evening, the second-hand clothing area for men and women, walking in and out of shops, the prices are lovely and affordable. There are many hip shops, vintage clothing, various brands. 📍Shimokitazawa I''ve been to Tokyo many times, and this was my first time shopping for secondhand clothes.', NULL, 0.9310187, '2026-03-17 18:47:02.967841+00'),
	(580, NULL, 'tokyo', 'vintage', 'Shimokitazawa vintage clothing Tokyo best shops 2026', 'https://bokksu.com/blogs/news/discover-shimokitazawa-a-trendsetter-s-guide-to-tokyo-s-hippest-neighborhood?srsltid=AfmBOop-dUcK8s8U8wmrsIgdsB7MFlxm8dtE8QFUMp7up5S7j2NWi_Cu', 'This vibrant neighborhood is home to some of the best vintage and thrift shops in Japan and is a must-visit destination for lovers of fashion, music, and artisan treats. Although the neighborhood is not among the largest in Tokyo, it’s famous for the many vintage shops, thrift fashion stores, cafes, live music theaters, and bars that line its streets. Most of these businesses, from standalone shops to fashion chains, sell second-hand and vintage clothing items. The following is a brief guide to the best thrift shops for fashion enthusiasts in Shimokitazawa:. **TreFacStyle (Treasure Factory Style):** Owned by popular Japanese chain Treasure Factory, the two TreFacStyle stores in Shimokita are some of the most popular thrift shops in Tokyo. While both shops offer spectacular used fashion items, we recommend that you visit the larger one for more options. ==https://www.bokksu.com/collections/bokksu-exclusive-box-and-bundle/products/the-kawaii-gift-box==. Next time you visit Tokyo, remember to take a day trip to Shimokita and shop for affordable vintage fashion items.', NULL, 0.76490957, '2026-03-17 18:47:02.972344+00'),
	(581, NULL, 'tokyo', 'vintage', 'Shimokitazawa vintage clothing Tokyo best shops 2026', 'https://tokyocheapo.com/locations/west-tokyo/shimokitazawa-2/', '# Shimokitazawa. Shimokitazawa — often shortened to Shimokita — is a laid-back neighborhood just a few train stops from central Tokyo. ## Where is Shimokitazawa? ## What is Shimokitazawa like? Shimokitazawa was originally a farming community, and to this day it hasn’t lost its laid-back attitude — despite its close proximity to some of the busiest parts of Tokyo. Shimokita ranks among Tokyo’s best spots for thrift shopping and vintage clothes, with more than a few well-known vintage clothing chains, such as Chicago and Flamingo, as well as many smaller independent shops like Jarmusch or Link Ray. ## What to see and do in Shimokitazawa. used record shops shimokitazawa tokyo. ## Shopping in Shimokitazawa. Shopping in Shimokitazawa is all about vintage and thrifting. ## How to get to and from Shimokitazawa. ### The Best Things to Do in Shimokitazawa. used record shops shimokitazawa tokyo. ### Used Record Shopping in Shimokitazawa. ## Things To Do in Shimokitazawa. ## Shopping in Shimokitazawa.', NULL, 0.7187726, '2026-03-17 18:47:02.974875+00'),
	(582, NULL, 'tokyo', 'vintage', 'Shimokitazawa vintage clothing Tokyo best shops 2026', 'https://www.tripadvisor.com/AttractionProductReview-g1066455-d34019693-Tokyo_Shimokitazawa_Private_Vintage_Local_Gems_Tour-Setagaya_Tokyo_Tokyo_Prefectu.html', 'Explore RAGLAMAGLA, a top vintage-shop in Shimokitazawa where the unexpected meets style! With over a thousand items—from U.S./European antiques to modern', NULL, 0.71377134, '2026-03-17 18:47:02.978392+00'),
	(5, NULL, 'tokyo', 'vintage', 'Shimokitazawa vintage clothing Tokyo best shops 2026', 'https://japantravel.navitime.com/en/area/jp/guide/NTJtrv1113-en/', 'BIG TIME is a solid vintage and used clothing shop that has eleven outlets in Japan. ... Hickory is one of the oldest used clothing shops in Shimokitazawa. This', NULL, 0.99997437, '2026-03-17 03:29:00.881708+00'),
	(583, NULL, 'tokyo', 'vintage', 'Shimokitazawa vintage clothing Tokyo best shops 2026', 'https://wawojapantours.com/shimokitazawa-and-koenji-tokyos-vintage-clothing-treasure-troves/', 'Culture & History, Local Japan, Things To Do. Cafe, Jazz, Koenji, Second Hand Clothing, Second Street, Shimokita, Shimokitazawa, Treasure Factory, 古着. # Shimokitazawa and Koenji: Tokyo’s Vintage Clothing Treasure Troves. For anyone interested in digging through racks of vintage clothes, unearthing a heavily discounted Patagonia jacket in almost perfect condition, or simply wandering through alleys lined with smokey yakitori stands, these two neighborhoods are essential stops. Just a few stops from Shinjuku or Shibuya, the area is a maze of narrow streets filled with cafés, small live houses, and, most importantly, vintage clothing shops. Wander the covered shopping streets, or duck into side alleys, and you will find everything from small hole-in-the-wall vintage boutiques to multi-floor second-hand emporiums. Second Street and Treasure Factory are here too, but Koenji’s identity really shines in its independent stores. Shimokitazawa and Koenji share a love for vintage and second-hand clothing, but they each have a distinct flavor. **Shimokitazawa** feels trendier, a bit more polished, and has a larger presence of well-organized chain stores like Second Street and Treasure Factory.', NULL, 0.68496037, '2026-03-17 18:47:02.981786+00'),
	(584, NULL, 'tokyo', 'vintage', 'Koenji vintage clothing shops Tokyo', 'https://narrow-road.office-natsu.net/food/koenji/', 'Location of Koenji Vintage Clothing Stores. When strolling along the street where vintage clothing stores gather in Koenji, it’s challenging to come across shops dealing in new clothing. However, the cluster of vintage clothing stores in Koenji is concentrated along the road connecting Shinkoenji Station (marked as B on the map) of Marunouchi (Metro) Line and Koenji Station (marked as A on the map). If you get off at Koenji Station  (marked as A on the map) and head south from the south exit along the Koenji Pal Shopping Street arcade, you’ll find one vintage clothing store after another. If you alight at Shinkoenji Station (marked as B on the map), heading north along the Shinkoenji Street will quickly lead you to an area where vintage clothing stores line up. Koenji PAL Shopping Street, Vintage Clothing Stores, Koenji Walking Guide. * Vintage clothing stores are concentrated along particular streets, such as the Koenji Pal Shopping Street arcade and Shinkoenji Street.', NULL, 0.9134376, '2026-03-17 18:47:07.801414+00'),
	(10, NULL, 'tokyo', 'vintage', 'Koenji vintage clothing shops Tokyo', 'https://www.reddit.com/r/ThrowingFits/comments/16rzvf9/japan_trip_need_best_thrift_clothing_stores_jawn/', 'Go to an area in Tokyo called Koenji. It''s like all vintage clothing stores. Absolute must. I spent like a full day there. Favourite store was Safari 4.', NULL, 0.99995565, '2026-03-17 03:29:06.530983+00'),
	(35, NULL, 'tokyo', 'shopping', 'Don Quijote Tokyo what to buy souvenirs', 'https://www.youtube.com/watch?v=65KOmNv5sG0', '... Gifts 7:43 Beauty (with $50 budget) 11:41 More Beauty 18:11 Another store I love! 10+ POPULAR Japanese Beauty Products You MUST BUY In', NULL, 0.9997198, '2026-03-17 03:29:36.452122+00'),
	(585, NULL, 'tokyo', 'vintage', 'Koenji vintage clothing shops Tokyo', 'https://experience-suginami.tokyo/2018/10/koenji-southeast-vintage-clothing-district/', '* KOENJI SOUTHEAST VINTAGE CLOTHING AREA. ## KOENJI SOUTHEAST VINTAGE CLOTHING AREA. While the west side offers more organization in the way that all the clothing shops are lined up down Pal Street, Etoile Dori Street, and Look Street, shops on the east side are scattered about everywhere south of Koenji Station and east of the Konan Dori Street. A handful of shops are clustered in the area just south of Hikawa Shrine (Green Light, Hiraru, Laugh, Shinto, etc.) and more open up on the street heading south from there (Whistler, Chart, Gasoline, S.O, Re’all, Fifty-Fifty), and there are many more scattered about the area. Your time here could be spent shopping at the unique shops, checking out the shrine, relaxing in Koenji Chuo Park, and drinking coffee at Poem, the Japanese coffee shop at the beginning of the area. **Location:** The vintage clothing area on the southeast side of Koenji is located east of Konan Dori Street, the main road that heads south from Koenji Station. Long Shopping Street in Koenji''s Southern Area.', NULL, 0.89720124, '2026-03-17 18:47:07.807238+00'),
	(586, NULL, 'tokyo', 'vintage', 'Koenji vintage clothing shops Tokyo', 'https://www.tripadvisor.com/AttractionProductReview-g1066458-d27135794-Tokyo_Vintage_Clothing_Tour_in_the_Vintage_Town_Koenji-Suginami_Tokyo_Tokyo_Prefe.html', 'In this tour, you will visit four vintage clothe stores in Koenji, a town where you can find rare vintage clothes that are hard to find even in the United', NULL, 0.8452414, '2026-03-17 18:47:07.810417+00'),
	(587, NULL, 'tokyo', 'vintage', 'Koenji vintage clothing shops Tokyo', 'https://japantravel.navitime.com/en/area/jp/guide/NTJtrv1102-en/', 'The staff handpicks all the vintage clothing from second hand stores in America and these frequent trips call for a wide variety of eccentric styles. The store also carries some non-used brand collections from "dearie dada" and "desperate", both of which carefully design items to suit various vintage styles. This retro-style vintage store specializes in womenswear, with a focus on pop and psychedelic patterned items from the 1960s to 1980s (the golden age of the Showa era). The staff handpicks all the vintage clothing from second hand stores in America and these frequent trips call for a wide variety of eccentric styles. The store also carries some non-used brand collections from "dearie dada" and "desperate", both of which carefully design items to suit various vintage styles. This retro-style vintage store specializes in womenswear, with a focus on pop and psychedelic patterned items from the 1960s to 1980s (the golden age of the Showa era).', NULL, 0.8116913, '2026-03-17 18:47:07.813432+00'),
	(588, NULL, 'tokyo', 'vintage', 'Koenji vintage clothing shops Tokyo', 'https://www.japanrailclub.com/thrifting-in-koenji-8-furugiya/?srsltid=AfmBOorWUgFBaTP-tc-I6sSlgovMIJmXf6hjO6brjQhQHHZ9C5eYLI-4', 'Probably one of the more eye-catching furugiya around Koenji, Whistler offers vintage and used clothing imported from the USA from the 1940s to 1960s for men.', NULL, 0.7366474, '2026-03-17 18:47:07.816221+00'),
	(15, NULL, 'tokyo', 'skincare', 'best skincare shops Tokyo Cosme Matsumoto Kiyoshi Loft Tokyu Hands must buy', 'https://www.instagram.com/p/DSwHbRhkmVj/', 'Tokyu Hands – Multi-floor store with beauty gadgets and skincare tools. •SKINGARDEN (Shinjuku) – Known for Japanese and Korean beauty brands.', NULL, 0.56258565, '2026-03-17 03:29:12.474007+00'),
	(589, NULL, 'tokyo', 'skincare', 'best skincare shops Tokyo Cosme Matsumoto Kiyoshi Loft Tokyu Hands must buy', 'https://www.drrachelho.com/blog/best-beauty-stores-skincare-makeup-tokyo-japan/', '@cosme Flagship Store in Harajuku is THE place to be to know which beauty products- hair, makeup, skincare, fragrances…etc are trending in Japan. The next place you must visit in Tokyo to get beauty products from low to mid priced brands is Matsumoto Kiyoshi Drugstore. Mitsukoshi Ginza is the place to buy high end J-beauty products; and from brands that are not available in Singapore. ##### **Highlights of shopping at Ainz & Tuple: Finding out @cosme award winners without the crowds, an interesting range of Asian beauty products and Ayura, Ainz & Tulpe’s in house skincare brand.**. The Shiseido global flagship store in Ginza also has a skin diagnostic system that provides a report about how your skin is doing, as well as product recommendations from the brand. These wonderful and fun shopping experiences aside, the Shiseido global flagship store in Ginza offers the entire range of Shiseido skincare and makeup products; some of which are not available in Singapore.', NULL, 0.79196626, '2026-03-17 18:47:12.611846+00'),
	(590, NULL, 'tokyo', 'skincare', 'best skincare shops Tokyo Cosme Matsumoto Kiyoshi Loft Tokyu Hands must buy', 'https://www.projectvanity.com/projectvanity/where-to-shop-for-beauty-products-in-japan-loft-tokyu-hands-cosme-its-demo', '# Where to shop for beauty products in Japan: Loft, Tokyu Hands, Cosme, It''s Demo. But what would a Japan trip be without invading my fave beauty stores? The 45 common Japanese beauty terms to help you survive shopping in Tokyo. The 45 common Japanese beauty terms to help you survive shopping in Tokyo. This is a chain store carrying a diverse range of seasonal gifts, stationery, and of course, beauty products. Though they’re not a primarily a cosmetics store, you can find a lot of the top-ranking Japanese beauty products here. Cosme is a popular Japanese rating site where users rate the best products in different beauty categories. But like in our local convenience store beauty challenge, you can get beauty products here in a pinch! **Gett’s Japan beauty shopping tips:**. * While cash is still king in most Japanese establishments like *konbini* and restos, you can use your credit card or even your IC card like Suica or Pasmo while shopping at most stores. Where do you shop for beauty products in Japan?', NULL, 0.62000114, '2026-03-17 18:47:12.620613+00'),
	(591, NULL, 'tokyo', 'skincare', 'best skincare shops Tokyo Cosme Matsumoto Kiyoshi Loft Tokyu Hands must buy', 'https://digjapan.travel/en/blog/id=11213', '1. Scalp D Eyelash Essence by ANGFA · 3. Chu Lip by ROHTO Pharmaceutical · 5. naturie Hato Mugi Skin Conditioner by imju · 6. Japanese Sake Toner and Lotion by', NULL, 0.6155738, '2026-03-17 18:47:12.622925+00'),
	(592, NULL, 'tokyo', 'skincare', 'best skincare shops Tokyo Cosme Matsumoto Kiyoshi Loft Tokyu Hands must buy', 'https://www.tiktok.com/@shelbyscafediary/video/7531217117849357586', 'Top 3 Cosmetics and Skincare Shops in Japan: Where to Shop! Discover top recommendations for cosmetics and skincare shopping in Japan, including', NULL, 0.58721006, '2026-03-17 18:47:12.625241+00'),
	(227, 'dotonbori', 'osaka', 'restaurant', 'Ichiran Ramen Dotonbori', 'https://ichiran.com/', 'Famous tonkotsu ramen chain with solo booth dining. Customizable broth richness, noodle firmness, garlic level. Expect queues. ~¥990/bowl.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(228, 'dotonbori', 'osaka', 'restaurant', 'Mizuno Okonomiyaki', NULL, 'Dotonbori landmark since 1945. Known for yama-imo (mountain yam) okonomiyaki cooked on teppan in front of you. ¥1,200+.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(593, NULL, 'tokyo', 'skincare', 'best skincare shops Tokyo Cosme Matsumoto Kiyoshi Loft Tokyu Hands must buy', 'https://www.instagram.com/reel/DUaZaRcDv2M/', 'Shiseido The Store (Ginza) – Luxury flagship for Japan''s top skincare brand. ... LOFT – Trendy lifestyle store with a great cosmetics and skincare', NULL, 0.57006866, '2026-03-17 18:47:12.627403+00'),
	(668, 'tokyo-ueno', 'tokyo', 'sakura', 'Ueno Park cherry blossom 2026 sakura forecast bloom', 'https://matcha-jp.com/en/23392', 'The best time to see the cherry blossoms in Ueno Park is typically from late March until early April. However, these dates can change depending on the weather', NULL, 0.7646988, '2026-03-17 18:48:35.235319+00'),
	(20, NULL, 'tokyo', 'skincare', 'Japanese face cream serum best buys tourists Tokyo 2026', 'https://www.reddit.com/r/AsianBeauty/comments/1q90tln/best_skincare_product_to_get_in_japan/', 'Best skincare product to get in Japan ? Best skincare product to get in Japan ? Hi guys, so I have planned a trip to Japan soon and I was wondering if there''s a skincare product that is a must buy. Look for Hada Labo Gokujyun (lotion/toner), Biore UV Aqua Rich, Anessa sunscreen, and Curel Intensive Moisture if you have sensitive skin. Melano CC serum - it’s amazing vitamin c, so affordable and the product itself feels so good on your skin. Melano CC serum, biore aqua rich sunscreen, hada labo premium hydrating lotion, and have fun experimenting with all different kinds of spf!! Their products contain Vaseline compounds to really lock in moisture—I’ve heard they were also a drugstore dupe for IPSA, a higher-end department store skincare brand (also popular in Japan)! I am 67 and go to Japan often: Get a set of Hada Labo in the gold line (Gokujyun) and the red line (Anti-aging) and also Melano CC and a little jar of tsubaki oil. Best skincare products to buy in Japan.', NULL, 0.9972638, '2026-03-17 03:29:18.140568+00'),
	(594, NULL, 'tokyo', 'skincare', 'Japanese face cream serum best buys tourists Tokyo 2026', 'https://livejapan.com/en/article-a0005789/', 'LIVE JAPAN offers a great coupon for foreign tourists, giving you 10% tax-free savings + up to an additional 7% OFF your shopping at Don Quijote. It’s time for Don Quijote’s DonCos Hit Award, where the hottest beauty products of the season take the spotlight. A long-time fan favorite, this Keana Nadeshiko Rice Mask is soaked in rich Rice Serum made from 100% Japanese-grown rice. Developed in collaboration with top cosmetics manufacturers from around the world, SEKACOS offers premium-quality beauty products at Don Quijote’s signature kyoyasu (astonishingly low) prices. Don Quijote is brimming with even more incredible cosmetics featuring Japan’s latest beauty innovations and trends. Let this guide be your starting point to discover your own personal must-haves at Don Quijote, and make the most of your beauty shopping adventure in Japan! Before you shop, don’t forget to use the LIVE JAPAN Don Quijote coupon for 10% tax-free + up to 7% off your purchase.', NULL, 0.99958915, '2026-03-17 18:47:17.415813+00'),
	(595, NULL, 'tokyo', 'skincare', 'Japanese face cream serum best buys tourists Tokyo 2026', 'https://www.youtube.com/watch?v=7gCrhxqK9Z0', 'Japan Drugstore Guide 2026 – What Tourists Should Buy ... Top Beauty Products To Buy In Japan | Japanese Skincare Products - Matsumoto Kiyoshi.', NULL, 0.9995197, '2026-03-17 18:47:17.423691+00'),
	(596, NULL, 'tokyo', 'skincare', 'Japanese face cream serum best buys tourists Tokyo 2026', 'https://www.cntraveller.com/article/japanese-skincare-these-are-the-products-i-buy-every-time-i-visit-japan-as-a-beauty-editor-of-15-years', 'But you don’t have to look too hard to find the best skin care products in Japan – they are everywhere. Unlike Western beauty traditions, which often pursued dramatic transformation, Japanese facial skincare historically focused on preservation – maintaining clear, luminous skin through layering lightweight formulas and effective sun protection. ## The best Japanese skincare products to buy. I always stock up in Japan because multipacks are cheaper and it’s one of the best Japanese face washes for good reason. If you’re hunting for the best skincare to buy in Japan, make it this SPF. Packed with multiple forms of hyaluronic acid, this is one of the best skin care products in Japan for good reason; because it’s a fast-track route to plump, glassy skin. This cult Japanese skincare-meets-make-up hybrid is an ultra-fine powder to even skin tone, soften the look of pores and reduce shine, leaving a translucent finish with subtle coverage.', NULL, 0.9983897, '2026-03-17 18:47:17.425524+00'),
	(597, NULL, 'tokyo', 'skincare', 'Japanese face cream serum best buys tourists Tokyo 2026', 'https://www.timeout.com/tokyo/shopping/best-japanese-skincare-products-drugstore', 'Best Japanese skincare products · Ihada Night Pack · Sana Soy Milk 6 In 1 Moisture Gel Cream · Pair Acne Cream · Saborino Face Masks · The Retinotime', NULL, 0.99821776, '2026-03-17 18:47:17.42771+00'),
	(25, NULL, 'tokyo', 'street_food', 'best street food Tokyo Yanaka Ginza Ameyoko vendors what to eat', 'https://www.youtube.com/watch?v=YuchaFQw3fU', 'Yanaka Ginza is one of the best Tokyo hidden secret street food areas. This is a Tokyo street food guide on what to eat and see.', NULL, 0.62934244, '2026-03-17 03:29:25.114464+00'),
	(599, NULL, 'tokyo', 'street_food', 'best street food Tokyo Yanaka Ginza Ameyoko vendors what to eat', 'https://www.facebook.com/groups/457573074653783/posts/1644747482602997/', '❤️✅️ Ameyoko is a bustling market street in the Ueno area of Tokyo, famous for its wide variety of street food, including takoyaki. Takoyaki, a', NULL, 0.9999635, '2026-03-17 18:47:22.237092+00'),
	(600, NULL, 'tokyo', 'street_food', 'best street food Tokyo Yanaka Ginza Ameyoko vendors what to eat', 'https://www.timeout.com/tokyo/restaurants/best-street-food-and-snacks-at-yanaka-ginza', 'This retro shopping street in Yanaka offers a good variety of Japanese snacks and desserts, from takoyaki to soft-serve.', NULL, 0.9998523, '2026-03-17 18:47:22.246447+00'),
	(601, NULL, 'tokyo', 'street_food', 'best street food Tokyo Yanaka Ginza Ameyoko vendors what to eat', 'https://www.magical-trip.com/media/recommended-street-foods-in-yanaka-ginza/', '# Recommended Street Foods in Yanaka Ginza 2026. If you want to experience Yanaka to the fullest—including its living traditions and culture—be sure to join the "**Yanaka Historical Walking Tour in Tokyo''s Old Town**" with local guides. If you want to experience the local side of Japan in Tokyo, Yanaka is highly recommended. Yanaka Ginza has plenty of street foods perfect for snacking during your walk. In this article, I''ll introduce some recommended street foods in Yanaka Ginza as someone who used to live nearby. When it comes to famous Yanaka Ginza street foods, the menchi katsu (minced meat cutlet) tops the list. As a tachinomi shop, you can order Japanese sake, beer, and bring in snacks purchased from other Yanaka Ginza shops like menchi katsu or ikayaki. To deepen your experience, I recommend joining a guided Yanaka Historical Walking Tour in Tokyo''s Old Town that covers all the highlights.', NULL, 0.99983907, '2026-03-17 18:47:22.252243+00'),
	(30, NULL, 'tokyo', 'shopping', 'Harajuku Omotesando shopping guide fashion youth culture', 'https://www.yokogaomag.com/tokyo-guide/harajuku', '# Harajuku Guide - Tokyo''s Core of Youth Culture and Fashion. Nestled between the districts of Shibuya and Shinjuku lies **Harajuku**, an eclectic neighborhood that serves as the beating heart of Tokyo''s youth culture and fashion scene. * **How to get to Harajuku**. Upon exiting Harajuku station, right at the center of Harajuku''s fashion frenzy lies **Takeshita Street**, often referred to as Harajuku Street, a bustling avenue lined with quirky shops, vibrant street food stalls, and a crowd with a mix of stylish locals and curious tourists. Make a quick first stop in a small side alley of Takeshita Street to discover an iconic shop that embodies modern-day Harajuku style, a significant influence on Tokyo''s youth. From the abundance of sweet treats on Takeshita street, to the savoury spots hidden a little deeper into the alleys of Tokyo’s fashion district, Harajuku knows how to please its guests. ### **How to get to Harajuku**. Harajuku Guide - Tokyo''s Core of Youth Culture and Fashion. Harajuku Guide - Tokyo''s Core of Youth Culture and Fashion.', NULL, 0.999972, '2026-03-17 03:29:30.859973+00'),
	(229, 'namba', 'osaka', 'restaurant', 'Takoyaki Wanaka', NULL, 'Best takoyaki near Namba. Crispy outside, creamy inside. Multiple sauce options. ~¥500 for 8 pieces.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(602, NULL, 'tokyo', 'street_food', 'best street food Tokyo Yanaka Ginza Ameyoko vendors what to eat', 'https://www.japan-experience.com/plan-your-trip/to-know/tokyo/japanese-food-and-drink/street-food-in-yanaka-ginza-eat-and-explore-in-retro-tokyo', 'Yanaka no Omusubi has mastered the classics, with offerings like tuna-mayo, salmon, squid and konbu, and ume plums being menu mainstays! However', NULL, 0.99974483, '2026-03-17 18:47:22.254883+00'),
	(603, NULL, 'tokyo', 'street_food', 'best street food Tokyo Yanaka Ginza Ameyoko vendors what to eat', 'https://www.byfood.com/blog/tokyo/best-tokyo-street-food-spots', '# Street Food in Tokyo: 10 Best Street Food Spots. Here are 10 of the best places to try Japanese street food in Tokyo. ## 10 Best Tokyo Street Food Spots. Here are the best spots to check out if you''re wondering where to find street food in Tokyo. After trying the fuku nyan-yaki in Yanaka Ginza, explore more sweet treats on a street food tour with an English-speaking guide in the Asakusa district, where you can learn about the history of its famous landmarks and taste ningyo-yaki shaped like Senso-ji’s five-story pagoda or Kaminarimon’s big lantern. It’s also a great place to try some traditional Tokyo street food such as fried and candied sweet potatoes, crispy rice crackers, and moist, pancake-like senbei. While browsing, refuel with Tokyo street food like imagawayaki pancakes filled with sweet potato or kare pan (Japanese curry bread) that''s perfectly crispy on the outside and deliciously doughy on the inside. ### Is street food in Tokyo safe?', NULL, 0.99938333, '2026-03-17 18:47:22.257794+00'),
	(604, NULL, 'tokyo', 'shopping', 'Harajuku Omotesando shopping guide fashion youth culture', 'https://www.gotokyo.org/en/story/guide/shibuya-shop/index.html', '# Shibuya, Harajuku, and Omotesando Shopping Guide. Known as Tokyo''s fashion capital, Shibuya is home to many department stores. Address: 4-12-10 Jingumae, Shibuya City, Tokyo. Address: 2-21-1 Shibuya, Shibuya City, Tokyo. ## Shibuya Style: The Hottest in Tokyo''s Fashion Capital. Department stores and popular shops surround the famous Shibuya Crossing and line Omotesando Avenue, while Harajuku is a hub for fashionable young people. Located right down the street from Harajuku Station, on the corner of Omotesando-dori Street and Meiji-dori Street, it''s packed with clothing and culture stores to suit all your trendy shopping needs. Address: 1-11-6 Jingumae Shibuya City, Tokyo. Address: 2-29-1 Dogenzaka, Shibuya City, Tokyo. Address: 2F TX101 Building, 4-28-16 Jingumae, Shibuya City, Tokyo. Address: 6-25-10 Jingumae, Shibuya City, Tokyo. Address: TOKYU PLAZA OMOTESANDO HARAJUKU, 4-30-3 Jingumae, Shibuya City, Tokyo. ## Beyond Fashion: Home and Interior Shopping in Shibuya. Address: 1-24-12 Shibuya, Shibuya City, Tokyo. Address: 1-19-24 Jingumae, Shibuya City, Tokyo. Address: 6-1-9 Jingumae, Shibuya City, Tokyo. Address: 3-20-1 Jingumae, Shibuya City, Tokyo. Address: 22-2 2F Udagawacho, Shibuya City, Tokyo.', NULL, 0.8703443, '2026-03-17 18:47:29.427356+00'),
	(40, NULL, 'tokyo', 'temple', 'Senso-ji Asakusa tips avoid crowds best time visit', 'https://www.tripadvisor.com/ShowTopic-g298184-i861-k11333634-Sensoji_Temple_Meiji_Shrine_best_day_time_to_visit-Tokyo_Tokyo_Prefecture_Kanto.html', 'Early morning on weekdays are least crowded. It''s a good time to go to Meiji Jingu, but Asakusa is more fun after the shops at Nakamise open', NULL, 0.9999318, '2026-03-17 03:29:42.141732+00'),
	(605, NULL, 'tokyo', 'shopping', 'Harajuku Omotesando shopping guide fashion youth culture', 'https://www.gltjp.com/en/article/item/20270/', 'Aoyama, Harajuku, and Omotesando is one of Tokyo’s top shopping districts, and a major trendsetting hub. ## 9 Must-Visit Shopping Spots in Aoyama, Harajuku, and Omotesando. From Takeshita Street, a hub of Kawaii culture, to streets lined with luxury brands, Aoyama, Harajuku, and Omotesando is packed with great places to shop. A landmark shop in the Harajuku and Omotesando area, packed with popular characters. A landmark shop in the Harajuku and Omotesando area, packed with popular characters. This area is known as Ura-Harajuku, and along Cat Street you’ll find many relatively small shops, including stylish select shops and street-level stores from notable brands. In the trend-leading Aoyama, Harajuku, and Omotesando area, you’ll find plenty of cafés and dining spots, so you can enjoy great food in stylish spaces. ## 3 Popular Sightseeing Spots in Aoyama, Harajuku, and Omotesando to Visit While You Shop. We’ve introduced what makes the Aoyama, Harajuku, and Omotesando area so appealing, from a hub of youth fashion and culture to shopping streets lined with refined luxury brands.', NULL, 0.82492816, '2026-03-17 18:47:29.43553+00'),
	(606, NULL, 'tokyo', 'shopping', 'Harajuku Omotesando shopping guide fashion youth culture', 'https://www.harajuku-kawaii-tour.com/fashion/harajuku-fashion-guide-explore-tokyo-style/', 'Harajuku fashion is the beating heart of Tokyo’s youth culture — a playground where creativity, color, and rebellion coexist. This vibrant avenue — often featured in travel guides as the ultimate Harajuku fashion street — captures the spirit of Tokyo’s youth culture like nowhere else. join our **Harajuku Kawaii Tour** or **Fashion Experience Tour** — guided experiences led by locals who live and breathe kawaii culture every day. These **Harajuku fashion stores** aren’t just places to shop — they’re living galleries of creativity that continue to inspire designers worldwide. Exploring these **vintage shops in Harajuku** reveals a different side of Tokyo fashion — sustainable, nostalgic, and deeply personal. **Join our Harajuku Kawaii Tour** — a private fashion experience that takes you through Harajuku’s best shopping streets, from vintage finds to iconic kawaii boutiques. Each **Harajuku fashion experience** includes a walking tour through iconic locations — from colorful Takeshita Street to hidden alleys perfect for photos.', NULL, 0.818055, '2026-03-17 18:47:29.438632+00'),
	(607, NULL, 'tokyo', 'shopping', 'Harajuku Omotesando shopping guide fashion youth culture', 'https://www.genkimobile.com/harajuku-omotesando-guide/', '# Harajuku & Omotesando: Tokyo’s Fashion Icons. Harajuku and Omotesando streets meeting in Tokyo. This isn’t a fantasy—it’s the real-life experience of standing between Harajuku and Omotesando, two of Tokyo’s most famous fashion districts that are, impossibly, just a five-minute walk apart. The five-minute walk from Harajuku station to Omotesando isn’t just a short stroll; it’s a journey from one major cultural pole to another, highlighting the incredible diversity of Tokyo’s fashion landscape. ## A Walking Guide to Cat Street: Where Harajuku’s Creativity Meets Omotesando’s Cool. Tucked between Harajuku’s youthful energy and Omotesando’s polished elegance is the neighborhood’s secret weapon: Cat Street. Beyond just being a shopping destination, Cat Street also functions as a fantastic and scenic walking route connecting the Harajuku area to the famous Shibuya district. **Short answer:** Follow Cat Street for a relaxed, scenic route that bridges Harajuku’s creativity with Omotesando’s cool—lined with indie boutiques, curated vintage, and global streetwear (think limited-edition sneakers and stylish lifestyle shops).', NULL, 0.81418616, '2026-03-17 18:47:29.441474+00'),
	(609, NULL, 'tokyo', 'shopping', 'Don Quijote Tokyo what to buy souvenirs', 'https://matcha-jp.com/en/24885', 'Discover the must-buy skincare products, snacks, and popular souvenirs available at Don Quijote discount stores in Japan. Includes a 17% discount coupon!', NULL, 0.6991933, '2026-03-17 18:47:34.23871+00'),
	(45, NULL, 'tokyo', 'temple', 'lesser known temples Tokyo hidden gems alternatives', 'https://www.youtube.com/watch?v=SZXoQUx7PZ8', '... shrines, some less popular and a hidden gem shrine you do not want to miss. There are so many temples (2872) and shrines (1450) in the Tokyo', NULL, 0.53881395, '2026-03-17 03:29:48.160559+00'),
	(610, NULL, 'tokyo', 'shopping', 'Don Quijote Tokyo what to buy souvenirs', 'https://www.reddit.com/r/JapanTravel/comments/106gkhf/what_do_you_love_to_buy_from_don_quijote_in_japan/', 'Towels, socks, tote bags, onesies, miniatures, snacks (just bought a slew of those collector cards wafers the other day), etc. Also a special', NULL, 0.6884899, '2026-03-17 18:47:34.246869+00'),
	(611, NULL, 'tokyo', 'shopping', 'Don Quijote Tokyo what to buy souvenirs', 'https://sumifuku.net/10-products-from-don-quijote-that-all-first-time-travellers-should-buy/', '# 10 Great Gifts To Buy From MEGA Don Quijote! Given that so many of these flavours are pretty niche, your friends and family back home are likely not to have tried them, making them a great gift. This cult-favourite hair mask makes hair look shiny and soft and makes an ideal gift for those who like to pamper themselves. This cult-favourite hair mask makes hair look shiny and soft and makes an ideal gift for those who like to pamper themselves. **Related Article: 8 Japanese Popular Skincare Brands to Try & Buy at Don Quijote**. Don Quijote stocks a good variety of Japanese traditional and fun board and card games. Of course, such items would take up a good bit of luggage space but they are a fun and practical gift which families and children will likely love! ### 10 Great Gifts To Buy From MEGA Don Quijote! ### Shibuya LOFT: Top 5 Gifts To Buy from The Largest Store in Japan.', NULL, 0.6186197, '2026-03-17 18:47:34.257574+00'),
	(612, NULL, 'tokyo', 'shopping', 'Don Quijote Tokyo what to buy souvenirs', 'https://livejapan.com/en/in-tokyo/in-pref-tokyo/in-shibuya/article-a0005325/', '1) Standard Popular Medicines · 2) Compresses & Adhesives · 3) Collagen Supplements · 4) Skin-Brightening Supplements · 5) Foot Relaxation Sheets · 6', NULL, 0.588062, '2026-03-17 18:47:34.260891+00'),
	(50, NULL, 'tokyo', 'events', 'Tokyo events late March April 2026 hanami sakura festivals', 'https://en.motenas-japan.jp/cherry-blossom-festival-japan/', 'Festival Period: During cherry blossom season (late March – early April). Reservation: Not required. Paid Seating: No official paid seating.', NULL, 0.7608822, '2026-03-17 03:29:54.844006+00'),
	(613, NULL, 'tokyo', 'shopping', 'Don Quijote Tokyo what to buy souvenirs', 'https://www.youtube.com/watch?v=2M5fs9fwaM8', '... Don Quijote Shibuya https://www.donki.com/en/store/shop_detail.php?shop_id=442 28-6 Udagawa-cho Shibuya-ku Tokyo,JAPAN, 150-0042 ============', NULL, 0.585789, '2026-03-17 18:47:34.263665+00'),
	(614, NULL, 'tokyo', 'temple', 'Senso-ji Asakusa tips avoid crowds best time visit', 'https://www.facebook.com/groups/planmyjapanforum/posts/1019686953473150/', 'Best time is early morning, although shops aren''t open. There is a 7-11 across the street at Thunder Gate. Late at night too. No crowds.', NULL, 0.8875269, '2026-03-17 18:47:39.101356+00'),
	(615, NULL, 'tokyo', 'temple', 'Senso-ji Asakusa tips avoid crowds best time visit', 'https://meetrip.to/asakusa_4/', 'New Year''s Day is arguably both the best and worst time to visit Asakusa''s Sensoji Temple. It can be interesting for foreigners because the days after New Years is probably the most crowded you will ever see Asakusa''s Sensoji Temple. New Year''s Day is arguably both the best and worst time to visit Asakusa''s Sensoji Temple. It can be interesting for foreigners because the days after New Years is probably the most crowded you will ever see Asakusa''s Sensoji Temple. New Year''s Day is arguably both the best and worst time to visit Asakusa''s Sensoji Temple. It can be interesting for foreigners because the days after New Years is probably the most crowded you will ever see Asakusa''s Sensoji Temple. New Year''s Day is arguably both the best and worst time to visit Asakusa''s Sensoji Temple. It can be interesting for foreigners because the days after New Years is probably the most crowded you will ever see Asakusa''s Sensoji Temple.', NULL, 0.79119295, '2026-03-17 18:47:39.104173+00'),
	(616, NULL, 'tokyo', 'temple', 'Senso-ji Asakusa tips avoid crowds best time visit', 'https://en.miyakodori-geisha.com/2025/07/16/when-is-the-least-crowded-time-in-asakusa-the-complete-guide-to-avoid-crowds-and-enjoy-comfortably/', '4. When is the Least Crowded Time in Asakusa? # When is the Least Crowded Time in Asakusa? Asakusa is always bustling with many visitors, but some may wish to avoid the crowds and quietly enjoy its atmosphere. However, **by adjusting your visiting times, days, and routes slightly, you can encounter a peaceful and quiet side of Asakusa away from the hustle and bustle**. This article will thoroughly introduce specific methods to avoid the crowds that have long captivated many people and to enjoy Asakusa’s attractions to the fullest. [Time-specific] When is Asakusa the Least Crowded? Asakusa, bustling with many tourists, can be enjoyed more comfortably by adjusting your visiting times. Following the early-morning calm, weekday mornings are the next best time to enjoy Asakusa with fewer people. Even though these times are crowded, they offer a rare chance to experience the festive and cultural spirit of Asakusa. Hidden Attractions in Asakusa to Visit Away from the Crowds.', NULL, 0.76512027, '2026-03-17 18:47:39.106635+00');
INSERT INTO public.knowledge_items (id, anchor, city, category, topic, source_url, content_summary, raw_content, tavily_score, ingested_utc) VALUES
	(55, 'tokyo-sugamo', 'tokyo', 'restaurant', 'best ramen restaurants near Sugamo Toshima Tokyo', 'https://tokyoramenoftheyear.com/en/near/tokyo/toshima-ku', 'Ramen shops near Toshima-ku Tokyo · Japanese Ramen Gokan · Sosakumenkobo NAKIRYU · Menpo Juroku · Miso Noodle House Tasakaya · Marue Chinese Noodles · Mensouan Sunada.', NULL, 0.7961819, '2026-03-17 03:30:00.561075+00'),
	(618, NULL, 'tokyo', 'temple', 'Senso-ji Asakusa tips avoid crowds best time visit', 'https://www.youtube.com/watch?v=bnRGmNvE40s', 'Sensōji Temple 6:45am is the best time to visit Sensoji Temple! It was very peaceful with only a handful of people. Sensoji Temple also', NULL, 0.7197191, '2026-03-17 18:47:39.109842+00'),
	(619, NULL, 'tokyo', 'temple', 'lesser known temples Tokyo hidden gems alternatives', 'https://www.travelynotes.com/blog-japan/hidden-gems-in-tokyo-unique-places-to-discover-beyond-the-tourist-spots', 'Beyond famous spots such as Shibuya Crossing, Senso-ji Temple, and Tokyo Skytree, there are so many hidden gems and lesser-known places that I was lucky enough to discover during the four years I lived in this wonderful city. In this list of Tokyo''s hidden gems, I have included practical tips such as the nearest train stations, admission prices (if any), and other interesting places nearby, as well as links to more detailed guides when I have written them. 📍**Horin-ji temple, Nishiwaseda, Shinjuku City, Tokyo**. Gotoku-ji, Discover Tokyo’s Cat Temple**. **📍Gotoku-ji temple, Gotokuji, Setagaya City, Tokyo**. **Shibamata** (柴又) feels like stepping back into old Tokyo, with its retro shopping street called **Taishakuten Sandō** (帝釈天参道), traditional sweets shops, and **Taishakuten temple** (柴又帝釈天), a beautiful Buddhist temple where you can admire stunning wooden carvings gallery as well as a charming Japanese garden. ➡️ Read my full guide here: **Autumn Walk Around Jindai-ji: Discover Tokyo’s Hidden Gem for Fall Foliage****.**.', NULL, 0.78314424, '2026-03-17 18:47:43.902783+00'),
	(231, 'shinsekai', 'osaka', 'restaurant', 'Daruma Kushikatsu', NULL, 'Shinsekai famous deep-fried skewers (kushikatsu). Iconic ''no double-dipping!'' rule for communal sauce. ¥100-200 per stick.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(233, 'shinsaibashi', 'osaka', 'restaurant', 'Pablo Cheese Tart', NULL, 'Shinsaibashi location. Freshly baked cheese tarts with rare/medium/well-done options. ~¥800.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(236, 'tenjinbashi', 'osaka', 'restaurant', 'Menya Jikon (麺や而今)', NULL, 'Tenjinbashi area ramen shop. Shoyu-based with clear refined broth. Michelin Bib Gourmand. ~¥950. Expect a wait.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(60, 'tokyo-sugamo', 'tokyo', 'temple', 'Koganji Temple Sugamo Togenuki Jizo shopping street guide', 'https://sugamo.or.jp/en/easy_method/', 'Sugamo Jizou-dori Shopping Street, which is known as the “Harajuku for Old Ladies”, is located on the former Nakasendo highway, and has thrived as a place of commerce and faith from the mid-Edo period to the present day. Later, in 1891, the Togenuki Jizouson of Koganji Temple was relocated from Ueno (an area that is now adjacent to Ueno’s Shinkansen station) to Sugamo, and today Sugamo Jizou-dori Shopping Street is protected by two Jizou Guardians, the “Tokenuki Jizouson” and the “Edoroku Jizouson”, as well as Sugamo Koshinzuka. Sugamo Jizou-dori Shopping Street, with its array of temples, street stalls, and small shops, is a place where not only classic Japanese scenery and culture, but also human kindness and old-fashioned shopkeepers’ hospitality are valued. * **From JR Sugamo Station to Sugamo Jizou-dori Shopping Street**. * **From Sugamo Station on the Toei Subway Mita Line to Sugamo Jizou-dori Shopping Street**. * **From Tokyo Sakura Tram Koshinzuka Station to Sugamo Jizou-dori Shopping Street**. * **From JR Otsuka Station to Sugamo Jizou-dori Shopping Street**.', NULL, 0.9999815, '2026-03-17 03:30:05.974846+00'),
	(620, NULL, 'tokyo', 'temple', 'lesser known temples Tokyo hidden gems alternatives', 'https://www.japansophy.com/post/10-lesser-known-temples-and-shrines-in-tokyo', '# 10 lesser-known temples and shrines in Tokyo worth visiting. In this article, we''ll explore ten lesser-known temples and shrines that offer beauty, cultural depth, and tranquility beyond the well-trodden tourist paths. **Access:** 10–12 minutes’ walk from Todoroki Station on the Tōkyū Ōimachi Line. **Hours:** Grounds open year-round; main hall typically from 9:00–17:00. **Hours:** Grounds open daily; shrine office typically 9:00–17:00. **Hours:** Grounds open daily; main hall from around 9:00–17:00. The tranquil grounds are full of hidden paths, small sub-temples, old cemeteries, and seasonal flora - especially lovely during cherry blossom season. **Access:** 3–5 minutes’ walk from Akasaka-mitsuke or Nagatachō Stations. **Hours:** The grounds are open all year round; most shrine buildings are accessible from early morning through late afternoon (e.g., 5 am–5 pm, depending on season). **Access:** 1 minute from Tsukiji Station (Hibiya Line). **Access:** 1–2 minutes from Sengakuji Station (Asakusa Line). You''re never far in Japan from a little shrine or temple that will charm, surprise, delight you.', NULL, 0.68874115, '2026-03-17 18:47:43.910783+00'),
	(621, NULL, 'tokyo', 'temple', 'lesser known temples Tokyo hidden gems alternatives', 'https://matadornetwork.com/watch/tokyo-hidden-temples/', '# The 5 Hidden Temples in Tokyo You Need to Visit. These are the hidden temples you might not find on a busy thoroughfare, but are worth taking the extra time to discover. ## Zojo-ji Temple. Zojo-ji is a relatively hidden temple located in Tokyo’s Shiba Park district. The temple was founded in 1393 and has been through a number of incarnations over the centuries. The current building dates back to 1457, making it one of the oldest temples in Tokyo. It’s one of the best temples in Tokyo for travelers interested in Japanese history and culture. ## Kantai-ji Temple. Kantai-ji is located in Nakano, an area of Tokyo known for its vibrant arts scene. ## Marishiten Tokudaiji Temple. Located in the heart of Tokyo, this temple is known for its beautiful architecture and stunning gardens. The temple grounds are surrounded by trees, making it feel like you’ve stepped into another world, and as you explore the grounds you’ll find several shrines and statues dedicated to Marishiten. ## Kotoku-in Temple.', NULL, 0.57952, '2026-03-17 18:47:43.913975+00'),
	(622, NULL, 'tokyo', 'temple', 'lesser known temples Tokyo hidden gems alternatives', 'https://www.tokyoweekender.com/things-to-do-in-tokyo/7-temples-in-tokyo-for-hatsumode/', '... less crowded and overwhelming experience. Consider visiting these seven alternative shrines for your first visit of the new year. List of', NULL, 0.49875546, '2026-03-17 18:47:43.916146+00'),
	(623, NULL, 'tokyo', 'temple', 'lesser known temples Tokyo hidden gems alternatives', 'https://www.japan-guide.com/forum/quereadisplay.html?0+178820', 'Re: What''s your Tokyo hidden gem? 2023/9/17 15:48. zozoji temple, with all of the little jizo. Maybe it is because it was the first place we', NULL, 0.4874788, '2026-03-17 18:47:43.918597+00'),
	(65, 'tokyo-sugamo', 'tokyo', 'local_market', 'Sugamo Jizo-dori shopping street what to buy', 'https://sugamo.or.jp/en/easy_method/', 'Sugamo Jizou-dori Shopping Street, which is known as the “Harajuku for Old Ladies”, is located on the former Nakasendo highway, and has thrived as a place of commerce and faith from the mid-Edo period to the present day. Later, in 1891, the Togenuki Jizouson of Koganji Temple was relocated from Ueno (an area that is now adjacent to Ueno’s Shinkansen station) to Sugamo, and today Sugamo Jizou-dori Shopping Street is protected by two Jizou Guardians, the “Tokenuki Jizouson” and the “Edoroku Jizouson”, as well as Sugamo Koshinzuka. Sugamo Jizou-dori Shopping Street, with its array of temples, street stalls, and small shops, is a place where not only classic Japanese scenery and culture, but also human kindness and old-fashioned shopkeepers’ hospitality are valued. * **From JR Sugamo Station to Sugamo Jizou-dori Shopping Street**. * **From Sugamo Station on the Toei Subway Mita Line to Sugamo Jizou-dori Shopping Street**. * **From Tokyo Sakura Tram Koshinzuka Station to Sugamo Jizou-dori Shopping Street**. * **From JR Otsuka Station to Sugamo Jizou-dori Shopping Street**.', NULL, 0.9999379, '2026-03-17 03:30:11.753059+00'),
	(624, NULL, 'tokyo', 'events', 'Tokyo events late March April 2026 hanami sakura festivals', 'https://www.facebook.com/groups/japantravel/posts/1028129671638946/', 'Naked Sakura festival at Nijo-Jo castle, Kyoto in March and April 2024. ... March 29 through April 12, 2026 and flying into and out of Tokyo.', NULL, 0.9999461, '2026-03-17 18:47:48.717391+00'),
	(669, 'ghibli-museum', 'tokyo', 'restaurant', 'restaurants near Ghibli Museum Mitaka Tokyo', 'https://savorjapan.com/contents/discover-oishii-japan/10-recommended-restaurants-near-mitaka-no-mori-ghibli-museum', '10 Recommended Restaurants Near the Ghibli Museum in Mitaka · 1. Yakitori Kappou Shouchan Kichijoji-bettei · 2. Asahikawa Jingisukan Daikokuya', NULL, 0.9125066, '2026-03-17 18:48:40.041423+00'),
	(670, 'ghibli-museum', 'tokyo', 'restaurant', 'restaurants near Ghibli Museum Mitaka Tokyo', 'https://www.tripadvisor.com/RestaurantsNear-g1060901-d581684-Ghibli_Museum-Mitaka_Tokyo_Prefecture_Kanto.html', 'Restaurants near Ghibli Museum · 1. Sushi Toiro. 5.0 · 2. Kafemugiwaraboshi. 4.0 · 3. Richoen Shimorenjaku · 4. · 5. Cafe du Lievre Usagikan · 6. Kirakunaomise · 7.', NULL, 0.90907925, '2026-03-17 18:48:40.046861+00'),
	(70, 'tokyo-sugamo', 'tokyo', 'pharmacy', 'pharmacy near Sugamo station Tokyo', 'https://sugamo.or.jp/en/shop/osdrug/', 'Industry. Pharmacy, cosmetics, etc. ; Name. Ōesu Drug ; Address. 4-22-1 Sugamo, Toshima-ku, Tokyo ; TEL. 03-5907-5938.', NULL, 0.99954873, '2026-03-17 03:30:17.625248+00'),
	(238, NULL, 'osaka', 'restaurant', 'Torikizoku', NULL, 'Popular budget chain izakaya. All food and drink items ¥350. Great for casual drinking and yakitori on a budget.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(248, 'umeda', 'osaka', 'restaurant', 'Yodobashi Umeda food court', NULL, 'Massive electronics store with excellent basement food court. Dozens of restaurants. Great rainy day option near Osaka Station.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(250, 'tsuruhashi', 'osaka', 'restaurant', 'Tsuruhashi Korean Town', NULL, 'Largest Korean district in Japan, near Tsuruhashi Station. Korean BBQ restaurants and kimchi shops everywhere. Lunch ~¥1,500.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(251, 'kitahama', 'osaka', 'restaurant', 'Bills Osaka', NULL, 'Australian-style brunch in Kitahama area. Famous ricotta pancakes and scrambled eggs. ~¥1,800. Weekend reservations recommended.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(75, 'tokyo-ueno', 'tokyo', 'museum', 'Tokyo National Museum highlights must see exhibits 2026', 'https://www.timeout.com/tokyo/art/best-art-exhibitions-in-tokyo-2026', 'Picasso and Paul Smith, Edo masterpieces, young British artists and sexy robots – Tokyo’s art slate looks packed this year. Then there’s a treasure trove of solo exhibitions highlighting domestic heavy hitters including Hajime Sorayama, Hiroshi Sugimoto and Minami Tada – the latter the focus of a long-awaited mega-retrospective at the Museum of Contemporary Art in autumn. K. Čiurlionis Art Museum in Kaunas, the exhibition will feature around 80 major works, including the Japanese debut of *The Altar* (1909) and the monumental masterpiece *Rex* (1909), the artist’s largest and most enigmatic painting. Marking the 100th anniversary of the Tokyo Metropolitan Art Museum, ‘Boundaries or Windows’ is the first major retrospective of Wyeth’s work in Japan since the artist’s death. From April 29 to September 23, the Mori Art Museum hosts the artist’s first solo exhibition in Japan in eighteen years. From August 29 to December 6, the Museum of Contemporary Art Tokyo presents the artist’s first solo exhibition in Tokyo in 35 years.', NULL, 0.99992573, '2026-03-17 03:30:24.297506+00'),
	(625, NULL, 'tokyo', 'events', 'Tokyo events late March April 2026 hanami sakura festivals', 'https://www.magical-trip.com/media/tokyo-in-april-2025-highlights-events-festivals/', '# Tokyo in April 2026: Highlights, Events & Festivals. In April 2026, this dynamic metropolis offers various events that showcase authentic Japanese experiences, including traditional shrine festivals, cherry blossom viewing (hanami) which symbolizes Japanese spring, and exceptional culinary events from across Japan. - 8-minute walk from Asakusa Station (Tokyo Metro). Tokyo has many popular cherry blossom viewing spots that reach peak bloom in April. ・****Ultimate Tokyo Seasonal Tours Guide 2026: Best Times to Experience Cherry Blossoms, Summer Festivals, Autumn Leaves & Winter Scenely**. The "Oedo Fukagawa Sakura Festival" is a cherry blossom viewing event where visitors can admire the spectacular rows of cherry trees blooming along the Oyoko River in the heart of metropolitan Tokyo. Another popular attraction of the "Oedo Fukagawa Sakura Festival" is the opportunity to enjoy cherry blossom viewing while riding traditional Japanese boats on the Oyoko River. - 5-minute walk from Kudanshita Station Exit 2 (Tokyo Metro and Toei Subway). ・****Ultimate Tokyo Seasonal Tours Guide 2026: Best Times to Experience Cherry Blossoms, Summer Festivals, Autumn Leaves & Winter Scenely**.', NULL, 0.999943, '2026-03-17 18:47:48.725008+00'),
	(626, NULL, 'tokyo', 'events', 'Tokyo events late March April 2026 hanami sakura festivals', 'https://www.gotokyo.org/en/story/guide/hanami-guide/index.html', '# When and where to see cherry blossoms in Tokyo in 2026. ## Cherry blossom season in Tokyo. Cherry blossom - or sakura - season in Tokyo is truly a magical experience. ## Best sakura festivals and cherry blossom viewing spots in Tokyo. ### Nakameguro Cherry Blossom Festival. If you’d like to enjoy even more cherry blossoms, head to the Sakura Festival in Chiyoda. In spring, the Ueno Sakura Matsuri is held around this cherry-tree avenue, drawing large crowds of cherry-blossom viewers. Every year during cherry blossom season, Koganei Cherry Blossom Festival takes place in late March in Koganei Park, and the Edo-Tokyo Open Air Architectural Museum in western Tokyo host a popular, lively event featuring folk entertainment and music. One such event is the Koganei Cherry Blossom Festival. The Koganei Cherry Blossom Festival takes place from late March to early April every year at the Edo-Tokyo Open Air Architectural Museum in Koganei Park.', NULL, 0.9996971, '2026-03-17 18:47:48.784523+00'),
	(627, NULL, 'tokyo', 'events', 'Tokyo events late March April 2026 hanami sakura festivals', 'https://en.japantravel.com/events/rpp%3D100?type=event&from=2026-04-01&to=2026-04-30&p=6', 'March 27th: Tokyo - Ark Hills Sakura Festival · March 28th: Tokyo - Machida Sakura Festival · March 28th: Yamagata - Yutagawa Onsen Plum', NULL, 0.9996513, '2026-03-17 18:47:48.84105+00'),
	(628, NULL, 'tokyo', 'events', 'Tokyo events late March April 2026 hanami sakura festivals', 'https://tour.tomogo-travel.com/blog/sakura-festivals-in-japan-2026', 'Spring in Japan isn’t just about seeing cherry blossoms, it’s about participating in **hanami**, the centuries-old tradition of gathering beneath sakura trees to appreciate their brief, beautiful bloom. Cherry blossoms covering Mount Yoshino in Nara during peak sakura season. Cherry blossom trees along the Sumida River during the Sumida Sakura Festival in Tokyo. Cherry blossoms illuminated at night along the Sumida River with Tokyo Skytree, during sakura season in Tokyo. Takato Castle Park covered in bright pink cherry blossoms during the sakura festival in Nagano, Japan. Cherry blossoms and lanterns during the Bunkyo Cherry Blossom Festival in Tokyo, Japan. Illuminated cherry blossoms at the Bunkyo Sakura Festival in Tokyo at night. If you’d like to experience sakura festivals in Japan at the right pace and in the right places, TOMOGO!’s seasonal cherry blossom tours are designed around real bloom timing and local insight.', NULL, 0.9994023, '2026-03-17 18:47:48.913366+00'),
	(80, 'tokyo-ueno', 'tokyo', 'market', 'Ameyoko market Ueno hours best things to buy street food', 'https://www.facebook.com/strictlydumpling/videos/10-must-try-foods-at-japans-original-black-market/1187280829678896/', 'Ueno Ameyoko Shopping Street is one of Tokyo''s most legendary food markets, packed with mouthwatering Japanese street food! From fresh sushi', NULL, 0.99983907, '2026-03-17 03:30:30.096629+00'),
	(629, 'tokyo-sugamo', 'tokyo', 'restaurant', 'best ramen restaurants near Sugamo Toshima Tokyo', 'https://www.yelp.com/search?cflt=ramen&find_loc=Sugamo+Station%2C+Toshima%2C+%E6%9D%B1%E4%BA%AC%E9%83%BD', 'The Best 10 Ramen near Sugamo Station, Toshima, 東京都, Japan · 1. 一蘭 池袋店 · 2. 磯丸水産 巣鴨北口店 · 3. 麺や いま村 · 4. 北大塚ラーメン · 5. 鳴龍 · 6. 千石自慢', NULL, 0.99995315, '2026-03-17 18:47:54.985786+00'),
	(630, 'tokyo-sugamo', 'tokyo', 'restaurant', 'best ramen restaurants near Sugamo Toshima Tokyo', 'https://www.yelp.com/search?cflt=ramen&find_loc=Toshima', 'Top 10 Best Ramen Near Toshima, 東京都 - With Real Reviews ; 1. 無敵家 · (123 reviews) ; 2. 一蘭 池袋店 · (69 reviews) ; 3. カラシビ味噌らー麺 鬼金棒 池袋店 · (20', NULL, 0.99991584, '2026-03-17 18:47:54.993677+00'),
	(631, 'tokyo-sugamo', 'tokyo', 'restaurant', 'best ramen restaurants near Sugamo Toshima Tokyo', 'https://www.tripadvisor.com/Restaurants-g1066460-zfd11722-Toshima_Tokyo_Tokyo_Prefecture_Kanto-Ramen.html', 'Top Ramen in Toshima ; 1. Mutekiya · (646 reviews). Japanese, Asian$$ - $$$. Open now. Their broth was delicious!! We had to wait in a queue', NULL, 0.9998579, '2026-03-17 18:47:54.997008+00'),
	(633, 'tokyo-sugamo', 'tokyo', 'restaurant', 'best ramen restaurants near Sugamo Toshima Tokyo', 'https://www.tripadvisor.com/Restaurants-g14134309-zfd11722-Sugamo_Toshima_Tokyo_Tokyo_Prefecture_Kanto-Ramen.html', 'Best Ramen in Sugamo, Toshima: Find Tripadvisor traveler reviews of THE BEST Ramen and search by price, location, and more.', NULL, 0.99978, '2026-03-17 18:47:55.000157+00'),
	(85, 'tokyo-ueno', 'tokyo', 'restaurant', 'best restaurants near Ueno Park Tokyo', 'https://www.reddit.com/r/JapanTravelTips/comments/1qtj4w5/ueno_food_recs/', 'For a memorial meal, Ningyocho Imahan at Ueno-Hirokoji is great, serving amazing traditional Sukiyaki. It''s quite pricey (6000 yen+), but the', NULL, 0.64773196, '2026-03-17 03:30:36.297766+00'),
	(254, 'amerikamura', 'osaka', 'restaurant', 'Cafe Absinthe', NULL, 'Amerikamura (American Village) bohemian cafe. Italian-Japanese fusion cuisine. Lunch ~¥900. Relaxed atmosphere.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(255, 'sumiyoshi', 'osaka', 'restaurant', 'Sumiyoshi Taisha area tea houses', NULL, 'Near Sumiyoshi shrine. Traditional matcha and wagashi (Japanese confections). ~¥500. Peaceful setting.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(634, 'tokyo-sugamo', 'tokyo', 'temple', 'Koganji Temple Sugamo Togenuki Jizo shopping street guide', 'https://www.gltjp.com/en/directory/item/10062/', '# Koganji Temple. Koganji Temple is also known as “Togenuki Jizou.” There exists an old legend that someone who swallowed a needle ate a piece of paper from Koganji Temple, and when the needle pierced the paper they were able to safely vomit it out. Furthermore, many people visit the temple for its “Arai Kannon,” a statue of Kannon that’s said to wash away ailments if you pour water on, and then polish with a cloth, the same part of the statue as the afflicted area. In front of the temple is “Sugamo Jizodori Shopping Street,” also known as the “Harajuku for old ladies,” where you can pick up items like Japanese sweets and retro Japanese products. * Entrance to Koganji Temple (Togenuki Jizou). Entrance to Koganji Temple (Togenuki Jizou). * Retro & Trendy Japan - A Travel Style Guide. If you have enabled domain-specific reception settings, please check your settings to ensure that emails from our site can be received.', NULL, 0.99999464, '2026-03-17 18:48:02.199002+00'),
	(635, 'tokyo-sugamo', 'tokyo', 'temple', 'Koganji Temple Sugamo Togenuki Jizo shopping street guide', 'https://www.tripadvisor.com/Attraction_Review-g14134309-d1373813-Reviews-Sugamo_Jizo_dori_Shopping_Street-Sugamo_Toshima_Tokyo_Tokyo_Prefecture_Kanto.html', 'One of the draws to the neighbourhood is the Kogan-ji temple(高岩寺), halfway down the shopping street , which boasts a statue of the folk deity Togenuki.', NULL, 0.99999464, '2026-03-17 18:48:02.204751+00'),
	(90, 'tokyo-ueno', 'tokyo', 'sakura', 'Ueno Park cherry blossom 2026 sakura forecast bloom', 'https://www.japanhighlights.com/japan/plan-a-cherry-blossom-trip', '# Japan''s Cherry Blossoms 2026 - Plan for the Full Bloom Now. **Japan''s cherry blossoms 2026 are expected to bloom from late March to early April** in the most popular central regions. The cherry blossom season is the most beautiful yet busiest time to travel in Japan. Spring is the cherry blossom season in Japan, but the blooming dates change each year. In 2026, the best time to see cherry blossoms in Honshu (Tokyo, Kyoto, etc.) is likely early April, around Easter. ## When is the Best Time to See Cherry Blossoms in Japan in 2026? We know you''d prefer to enjoy Japan without the stress of big spring crowds, and that''s exactly what we plan for you: an itinerary starting in mid-April, just after the peak rush, so you can still enjoy the beauty of cherry blossoms in a calmer, more relaxed way. You will view cherry blossoms in early April in Kyoto or Osaka.', NULL, 0.6824261, '2026-03-17 03:30:42.142466+00'),
	(636, 'tokyo-sugamo', 'tokyo', 'temple', 'Koganji Temple Sugamo Togenuki Jizo shopping street guide', 'https://japantravel.navitime.com/en/area/jp/spot/02301-1403492/', 'The Sugamo Jizo Dori Shopping Street has developed as the gateway to Kogan-ji Temple, and while the entire shopping street is filled with stalls on market days,', NULL, 0.9999865, '2026-03-17 18:48:02.206838+00'),
	(638, 'tokyo-sugamo', 'tokyo', 'temple', 'Koganji Temple Sugamo Togenuki Jizo shopping street guide', 'https://www.gotokyo.org/en/spot/46/index.html', 'GO TOKYO The Official Tokyo Travel Guide. What’s New in Tokyo. What''s On & Coming Up in Tokyo. Best Things to Do and See in Tokyo. Detailed search: You can do a detailed search by keyword, genre, time, area and tag. # Togenuki Jizo Kouganji Temple とげぬき地蔵尊 高岩寺. 3−35−2 Sugamo, Toshima City, Tokyo. ## Wash away your illnesses and pray for a long life at this historic Buddhist temple. If you have an ache or an ailment that has been bugging you, a visit to the Togenuki Jizo Kouganji Temple may just be the cure you need. Millions visit the historic Buddhist temple, located minutes by foot from Sugamo Station on the JR Yamanote Line, to pay their respects each year. The chief Buddhist image of the temple is the Enmei Jizo Bosatsu who, legend has it, has the powers to miraculously heal illnesses and extend one''s life. Copyright © Tokyo Convention & Visitors Bureau.', NULL, 0.9999461, '2026-03-17 18:48:02.209561+00'),
	(639, 'tokyo-sugamo', 'tokyo', 'local_market', 'Sugamo Jizo-dori shopping street what to buy', 'https://japanshopping.org/special/special_feature/detail/sugamo', '# Grandmother''s fashion street is full of retro - Sugamo Jizou Dori Shopping Street. Lined with individual stores along the old Nakasendo road, Sugamo Jizo-dori Shopping Street is a shopping street where you can immerse yourself in retro Japanese culture and find wonderful things that you would normally have forgotten about. Protected by two Jizo statues, “Edo Roku Jizoson” at Maseiji Temple and “Togenuki Jizoson” at Kowanji Temple, and Sugamo Koshinzuka, the 800-meter-long shopping street is crowded with many people who enjoy visiting and shopping. There are coffee shops and Japanese confectionery shops where you can hear the songs of the Showa period emanating from, and new stores, such as cafes and antenna stores, dotting the street. The Sugamo Jizo-dori Shopping Street is a shopping street where you can immerse yourself in retro Japanese culture and find wonderful things that you would normally have forgotten about. ・1 minute walk from Toei Mita line Sugamo Station, Exit A3. Tea shop at Sugamo Yamane-en.', NULL, 0.85967577, '2026-03-17 18:48:07.908373+00'),
	(671, 'ghibli-museum', 'tokyo', 'restaurant', 'restaurants near Ghibli Museum Mitaka Tokyo', 'https://wanderlog.com/list/geoCategory/198015/where-to-eat-best-restaurants-in-mitaka', 'Where to eat: the 50 best restaurants in Mitaka · 1 Ramen Bunzō · 2 Straw Hat Cafe (Ghibli Museum Cafe) · 3 Kujira Shokudo · 4 Tsukemen TETSU Mitaka · 5 Royal Host', NULL, 0.854509, '2026-03-17 18:48:40.050637+00'),
	(95, 'ghibli-museum', 'tokyo', 'restaurant', 'restaurants near Ghibli Museum Mitaka Tokyo', 'https://www.yelp.com/search?cflt=restaurants&find_near=%E3%82%B8%E3%83%96%E3%83%AA%E7%BE%8E%E8%A1%93%E9%A4%A8%E8%A1%8C%E3%81%8D%E3%81%AE%E5%B0%82%E7%94%A8%E3%83%90%E3%82%B9%E5%81%9C-%E4%B8%89%E9%B7%B9%E9%A7%85-%E4%B8%89%E9%B7%B9%E5%B8%82', '1. カフェ麦わらぼうし. Ghibli Museum Cafe · Bakeries · Sandwiches · Themed Cafes ; 2. ことりカフェ 吉祥寺. Kotoricafe Kichijoji · Themed Cafes ; 3. カフェ・ドゥ・', NULL, 0.75616, '2026-03-17 03:30:47.840231+00'),
	(672, 'ghibli-museum', 'tokyo', 'restaurant', 'restaurants near Ghibli Museum Mitaka Tokyo', 'https://en.japantravel.com/tokyo/ghibli-museum-s-straw-hat-cafe/30186', 'The Straw Hat Cafe is located in Ghibli Museum, Mitaka, Tokyo. It is a most adorable cafe with gorgeous interior that reminds you of Ghibli movies everywhere', NULL, 0.82994765, '2026-03-17 18:48:40.055293+00'),
	(100, 'ghibli-museum', 'tokyo', 'transit', 'how to get to Ghibli Museum from Sugamo Tokyo train', 'https://www.ghibli-museum.jp/en/hours-and-directions/', 'Ghibli Museum, Mitaka in Japan. Ghibli Museum, Mitaka in Japan. # Hours and Directions. ## Hours. ## Tickets. Entrance to the Ghibli Museum is strictly by advance purchase of a reserved ticket which specifies the entry date and time of the reservation. ## Directions. ### Ghibli Museum, Mitaka. 1-1-83 Shimorenjaku, Mitaka-shi, Tokyo 181-0013, Japan. Google Maps PDF（257 KB）. To JR Mitaka Station, take the JR Chuo Line, approximately 20 minutes from JR Shinjuku Station. From the south exit of JR Mitaka Station, it''s a 15-minute walk to the Museum. ### Bus. A community bus runs from JR Mitaka Station to the museum every 15 minutes during opening hours. | Fares (paid by) | Adult | 230 yen (cash) | 230 yen (IC card) |. | Child (Ages 7 to 12) | 120 yen (cash) | 50 yen (IC card) |. ## Tickets. All admission to the Ghibli Museum, Mitaka is by advance reservation only. #### Current Exhibition. #### Current Film.', NULL, 0.9987453, '2026-03-17 03:30:53.734142+00'),
	(257, 'tenjinbashi', 'osaka', 'shopping', 'Tenjinbashisuji Shotengai', NULL, 'Japan''s longest covered shopping arcade at 2.6km. Over 600 shops with local prices. Less touristy than Shinsaibashi.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(258, 'shinsaibashi', 'osaka', 'shopping', 'Shinsaibashi-suji', NULL, 'Main Osaka shopping street. Mix of international brands (Zara, H&M, Uniqlo) and local boutiques. Covered arcade.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(259, 'amerikamura', 'osaka', 'shopping', 'Amerikamura (American Village)', NULL, 'Osaka''s Harajuku equivalent. Vintage clothing, streetwear, record shops. ¥500-3,000 range. Young creative vibe.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(260, 'nipponbashi', 'osaka', 'shopping', 'Den Den Town (Nipponbashi)', NULL, 'Osaka''s Akihabara. Retro video games, anime figures, electronics, maid cafes. Multiple floors of otaku culture.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(261, 'namba', 'osaka', 'shopping', 'Kuromon Market', NULL, '"Osaka''s Kitchen" — fresh seafood, premium fruit, tamagoyaki, street food. Open 9am-5pm. Go hungry. Busiest 10am-2pm.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(263, 'umeda', 'osaka', 'shopping', 'Grand Front Osaka', NULL, 'Premium shopping complex near Osaka Station. Flagship stores, restaurants, innovation labs. Good rainy day activity.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(264, 'dotonbori', 'osaka', 'shopping', 'Don Quijote (Donki) Dotonbori', NULL, '24-hour discount megastore. Souvenirs, snacks, cosmetics, electronics, tax-free. Iconic Ferris wheel on building.', NULL, NULL, '2026-03-17 18:39:21.935577+00');
INSERT INTO public.knowledge_items (id, anchor, city, category, topic, source_url, content_summary, raw_content, tavily_score, ingested_utc) VALUES
	(270, 'shinsekai', 'osaka', 'shopping', 'Dagashi-ya in Shinsekai', NULL, 'Old-school Japanese penny candy shops (dagashi-ya). Nostalgic retro sweets ¥10-100. Fun for kids and adults.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(271, NULL, 'osaka', 'shopping', 'Rinku Premium Outlets', NULL, 'Near Kansai Airport. 200+ shops with 30-80% off. Good for last-day shopping before flight. Shuttle from airport.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(272, 'sumiyoshi', 'osaka', 'temple', 'Sumiyoshi Taisha', NULL, 'Oldest shrine in Osaka (3rd century). Iconic arched Taiko-bashi bridge. Predates Buddhist influence on shrine architecture. Free entry.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(273, 'tennoji', 'osaka', 'temple', 'Shitennoji Temple', NULL, 'Japan''s first officially commissioned Buddhist temple (593 AD). Monthly flea market on 21st-22nd. ¥300 inner precinct.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(274, 'osaka-castle', 'osaka', 'temple', 'Osaka Castle', NULL, 'Iconic Osaka landmark and museum. ¥600 entry. Observation deck with city views. Surrounding park is prime cherry blossom spot.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(275, 'dotonbori', 'osaka', 'temple', 'Hozenji Temple', NULL, 'Tiny temple tucked in Dotonbori alley. Moss-covered Fudo Myo-o statue — splash water on it for good luck in love/business.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(276, 'namba', 'osaka', 'temple', 'Namba Yasaka Shrine', NULL, 'Striking giant lion-head stage building (Ema-den). Very photogenic. Said to swallow bad fortune. Free entry.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(277, 'tenjinbashi', 'osaka', 'temple', 'Tsuyunoten Shrine', NULL, 'Near Tenjinbashisuji shotengai. Patron shrine of performing arts. Beautiful plum trees bloom in February.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(278, 'shinsekai', 'osaka', 'temple', 'Isshinji Temple', NULL, 'Unique temple near Shinsekai. Okotsu-butsu statues made from cremation ashes of the deceased. Fascinating and respectful.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(280, NULL, 'osaka', 'transit', 'ICOCA card', NULL, 'Rechargeable transit card. Buy at any JR or Metro station (¥500 deposit). Works on all Osaka trains, buses, and at convenience stores.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(286, 'tenjinbashi', 'osaka', 'transit', 'Tenjinbashisuji-Rokuchome Station', NULL, 'Major interchange: Sakaisuji Line + Tanimachi Line. Direct to Namba in 15 min. Convenient if staying in Tenjinbashi area.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(288, NULL, 'osaka', 'practical', 'International ATM locations Osaka', NULL, '7-Eleven (7-Bank), JP Post Office, Lawson ATM — all accept Visa/Mastercard. 7-Eleven is most reliable and everywhere.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(289, 'umeda', 'osaka', 'practical', 'Coin lockers Osaka Station', NULL, '¥400 small, ¥500 medium, ¥700 large per day. Located at JR Osaka Station Central Exit. Fill up by midday on weekends.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(290, 'namba', 'osaka', 'practical', 'Coin lockers Namba', NULL, 'Under Namba Walk underground mall. ¥400-600. Fill up by noon on weekends. Alternative: luggage storage at tourist info counter.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(298, 'tenjinbashi', 'osaka', 'practical', 'Daiso near Tenjinbashi', NULL, '100-yen shop for travel supplies, kitchen items, umbrellas, phone accessories. Everything ¥100 (some ¥200-500). Multiple Osaka locations.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(300, NULL, 'osaka', 'nara_daytrip', 'Nara Park deer', NULL, '1,200 free-roaming sacred deer. Buy shika-senbei (deer crackers) ¥200 at park vendors. Deer bow when you bow. Watch bags — they nibble everything.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(306, NULL, 'osaka', 'usj', 'USJ Express Pass', 'https://www.usj.co.jp/', '¥7,800-12,800 depending on day and attractions. HIGHLY recommended for Super Nintendo World and Harry Potter. Buy online in advance.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(307, NULL, 'osaka', 'usj', 'Super Nintendo World', NULL, 'Timed entry required on busy days. Get numbered ticket or buy Express Pass. Power-Up wristband (¥3,200) for interactive games.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(308, 'tenjinbashi', 'osaka', 'usj', 'First train to USJ from Tenjinbashi', NULL, 'Metro Sakaisuji Line to Nishikujo, transfer JR Yumesaki Line. ~45 min total. Arrive by 8:00 for rope drop. Park opens 8:30-9:00.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(311, 'omicho', 'kanazawa', 'restaurant', 'Omicho Market kaisendon', NULL, 'Seafood bowls (kaisendon) at market stalls. Fresh from Sea of Japan. ¥2,000-3,500. Best selection before 10am when fishermen deliver.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(314, 'kanazawa-station', 'kanazawa', 'restaurant', 'Tamazushi', NULL, 'Kanazawa Station area premium sushi. Uses local Sea of Japan fish. Lunch sets from ¥2,500. Good arrival/departure meal option.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(315, 'korinbo', 'kanazawa', 'restaurant', 'Itaru Honten', NULL, 'Famous izakaya near Korinbo. Known for sashimi and jibuni stew (Kanazawa''s signature duck/wheat-gluten dish). Reserve ahead. ~¥900 for jibuni.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(316, 'higashi-chaya', 'kanazawa', 'restaurant', 'Fumuroya Cafe', NULL, 'Higashi Chaya area cafe specializing in fu (wheat gluten) dishes and matcha. Traditional Kanazawa sweets. Elegant atmosphere.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(317, 'kenrokuen', 'kanazawa', 'restaurant', 'Hacchobo', NULL, 'Kaiseki (traditional multi-course) restaurant near Kenroku-en. Seasonal ingredients, beautiful presentation. Lunch from ¥5,500.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(319, 'katamachi', 'kanazawa', 'restaurant', 'Turban Curry', NULL, 'Rival Kanazawa curry institution. Katsu curry ¥850. Near Katamachi entertainment district. Dark rich roux is the signature.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(323, 'higashi-chaya', 'kanazawa', 'shopping', 'Hakuichi Gold Leaf shop', NULL, 'Higashi Chaya flagship store. Famous gold leaf ice cream (¥891). Gold leaf cosmetics, crafts, and edible gold souvenirs.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(324, 'kanazawa-station', 'kanazawa', 'shopping', 'Kanazawa Station Rinto', NULL, 'Shopping mall inside Kanazawa Station. Local crafts, Kanazawa sweets, omiyage (souvenirs). Convenient last-stop shopping.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(325, 'kenrokuen', 'kanazawa', 'shopping', 'Kutani pottery shops', NULL, 'Colorful Kanazawa ceramics (Kutani-yaki). Bold reds, greens, yellows. Kutani Kosen shop near Kenroku-en. ¥1,000-50,000 range.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(327, 'omicho', 'kanazawa', 'shopping', 'Omicho Market souvenir shops', NULL, 'Dried fish, gold leaf products, local sake, pickles. Good for edible souvenirs. Shops open 9am-5pm.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(328, 'hirosaka', 'kanazawa', 'shopping', 'Hirosaka area boutiques', NULL, 'Upscale shopping district between Kanazawa Castle and Katamachi. Independent boutiques, galleries, cafes.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(330, 'tatemachi', 'kanazawa', 'shopping', 'Tatemachi Street', NULL, 'Fashionable shopping street between 21st Century Museum and Katamachi. Cafes, boutiques, select shops.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(331, 'kenrokuen', 'kanazawa', 'temple', 'Kenroku-en Garden', NULL, 'One of Japan''s top 3 gardens. Stunning in every season — snow-covered yukitsuri in winter, cherry blossoms spring. ¥320 entry. Allow 1-2 hours.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(333, 'higashi-chaya', 'kanazawa', 'temple', 'Higashi Chaya District', NULL, 'Beautifully preserved geisha district with wooden tea houses from 1820s. Gold leaf shops, traditional cafes. Most photogenic area in Kanazawa.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(334, 'nishi-chaya', 'kanazawa', 'temple', 'Nishi Chaya District', NULL, 'Smaller, quieter geisha quarter on the west side. Fewer tourists. Myoryuji (Ninja Temple) is nearby.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(336, NULL, 'kanazawa', 'temple', 'D.T. Suzuki Museum', NULL, 'Minimalist museum honoring Zen Buddhist philosopher. Beautiful Water Mirror Garden for contemplation. ¥310. Near 21st Century Museum.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(338, 'nagamachi', 'kanazawa', 'temple', 'Nagamachi Samurai District', NULL, 'Preserved samurai residences with earthen walls and water channels. Nomura-ke house ¥550, one of Japan''s best samurai homes.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(339, NULL, 'kanazawa', 'museum', '21st Century Museum of Contemporary Art', NULL, 'Iconic circular glass building. Free public zone with Leandro Erlich''s ''Swimming Pool''. Paid exhibitions ¥1,200. Central location.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(340, 'kenrokuen', 'kanazawa', 'museum', 'Ishikawa Prefectural Museum of Art', NULL, 'Houses National Treasure ''Iroji'' textile (Kaga Yuzen masterwork). Japanese art and crafts. ¥370. Near Kenroku-en.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(348, 'kanazawa-station', 'kanazawa', 'practical', 'Coin lockers Kanazawa Station', NULL, 'East Exit of station. ¥400-700 per day. Fill up on weekends. Alternative: send luggage ahead via Yamato (Kuroneko) takkyubin service.', NULL, NULL, '2026-03-17 18:39:21.935577+00'),
	(640, 'tokyo-sugamo', 'tokyo', 'local_market', 'Sugamo Jizo-dori shopping street what to buy', 'https://www.byfood.com/blog/travel-tips/what-to-eat-in-sugamo', 'When wandering through Sugamo and Jizo Dori, you’ll find street food vendors and local shops selling traditional wares and wagashi sweets (including more mature and conservative fashion on sale). It has since kept its nostalgic feel, now catering to the oldies of Tokyo (think a demographic of 60+) with traditional street food, local clothing shops, wagashi sweet vendors, and more. Along Jizo Dori Shopping Street, Sugi Honey Products is a specialty honey shop in Sugamo where you can try the delicious premium ice cream or “soft cream” that features pieces of honeycomb inside! You can purchase isoage on sticks which makes for a portable Sugamo street food to enjoy while wandering through Jizo Dori. ## How to Access Sugamo Jizo Dori Shopping Street. Sugamo is not just the Harajuku equivalent for Tokyo’s elderly population, but it’s full of souvenir shopping opportunities and delicious street food to munch on as you wander through the nostalgic local stores.', NULL, 0.84183896, '2026-03-17 18:48:07.915886+00'),
	(641, 'tokyo-sugamo', 'tokyo', 'local_market', 'Sugamo Jizo-dori shopping street what to buy', 'https://www.timeout.com/tokyo/shopping/sugamo-jizo-dori', 'Clothing stores, souvenir shops and street food abound. Do as the locals and pick up a pair of lucky red underwear, or stop by Koganji Temple', NULL, 0.8312667, '2026-03-17 18:48:07.918839+00'),
	(642, 'tokyo-sugamo', 'tokyo', 'local_market', 'Sugamo Jizo-dori shopping street what to buy', 'https://www.tripadvisor.com/Attraction_Review-g14134309-d1373813-Reviews-Sugamo_Jizo_dori_Shopping_Street-Sugamo_Toshima_Tokyo_Tokyo_Prefecture_Kanto.html', 'Some days there''s a kind of street market down the middle of the street too, wit fresh vegetables and fish. You can also buy red underwear, which is held to be', NULL, 0.8190992, '2026-03-17 18:48:07.921334+00'),
	(643, 'tokyo-sugamo', 'tokyo', 'local_market', 'Sugamo Jizo-dori shopping street what to buy', 'https://www.instagram.com/reel/DHua085y63F/', 'You could even buy some red underwear for good luck from the famous Maruji store! Bonus points if you spot the Sugamo duck mascot:) Jizo Dori', NULL, 0.8116913, '2026-03-17 18:48:07.923489+00'),
	(644, 'tokyo-sugamo', 'tokyo', 'pharmacy', 'pharmacy near Sugamo station Tokyo', 'https://www.yelp.com/search?cflt=pharmacy&find_loc=Sugamo+Station%2C+Toshima%2C+%E6%9D%B1%E4%BA%AC%E9%83%BD', 'The Best 10 Pharmacy near Sugamo Station, Toshima, 東京都, Japan · 1. マツモトキヨシ池袋ショッピングパーク店 · 2. マツモトキヨシ池袋東口店 · 3. Tomod''s · 4. ぱぱす', NULL, 0.9999788, '2026-03-17 18:48:12.717531+00'),
	(645, 'tokyo-sugamo', 'tokyo', 'pharmacy', 'pharmacy near Sugamo station Tokyo', 'https://japantravel.navitime.com/en/area/jp/around/category/0503/?spot=01127-10001108632', 'Sugamo Station Front Orthopedic Clinic: Tokyo Toshima-ku Sugamo 3-20-17 AKA Building 1F-5F: 0m ; Nemunoki Pharmacy: Tokyo Toshima-ku Sugamo 1-chome 14-3: 9m.', NULL, 0.99984026, '2026-03-17 18:48:12.724942+00'),
	(646, 'tokyo-sugamo', 'tokyo', 'pharmacy', 'pharmacy near Sugamo station Tokyo', 'https://japantravel.navitime.com/en/area/jp/destinations/A02130013/spot/?categoryCode=0503023&page=1', 'Sundrug Sugamo Station South Exit Store: location icon Tokyo Toshima-ku Sugamo 1-15-1 Miyata Building 1F: Closed (09:00 - 22:00). Sundrug CVS Oku Ginza', NULL, 0.99978, '2026-03-17 18:48:12.727252+00'),
	(647, 'tokyo-sugamo', 'tokyo', 'pharmacy', 'pharmacy near Sugamo station Tokyo', 'https://oikawaiin.info/en/access/index.html', '* Oikawa Clinic — a 5-minute walk from JR Sugamo Station ▼. * Directions from the South Exit of JR Sugamo Station ▼. * Other Access Options (besides JR Sugamo Station South Exit) ▼. ## Oikawa Clinic — a 5-minute walk from JR Sugamo Station. ## Directions from the South Exit of JR Sugamo Station. Exit JR Sugamo Station from the South Exit. ## Other Access Options (besides JR Sugamo Station South Exit). ## Parking Near Sugamo Station. The closest pharmacy to Oikawa Clinic, located right next to SA Parking Sugamo 1-chome. The second closest pharmacy to Oikawa Clinic, situated between JR Sugamo Station South Exit and Oikawa Clinic. A large park located diagonally opposite Oikawa Clinic, serving as a landmark for those walking from Sugamo Station. A coffee shop located immediately outside the JR Sugamo Station South Exit. A karaage (fried chicken) shop located just across the crosswalk to the right, immediately after exiting JR Sugamo Station South Exit.', NULL, 0.99970406, '2026-03-17 18:48:12.729198+00'),
	(674, 'ghibli-museum', 'tokyo', 'transit', 'how to get to Ghibli Museum from Sugamo Tokyo train', 'https://www.reddit.com/r/ghibli/comments/1xmcbt/getting_to_the_ghibli_museum/', 'if you get a PASMO from the station upon arrival in Tokyo you can load money onto it and take the train subway and bus anywhere you need to go.', NULL, 0.7606688, '2026-03-17 18:48:44.948992+00'),
	(675, 'ghibli-museum', 'tokyo', 'transit', 'how to get to Ghibli Museum from Sugamo Tokyo train', 'https://www.japan-guide.com/e/e3041.html', 'The museum can be reached from Mitaka Station on the JR Chuo Line (15 minutes, 260 yen from Shinjuku Station). There are shuttle buses from the', NULL, 0.6708892, '2026-03-17 18:48:44.958499+00'),
	(676, 'ghibli-museum', 'tokyo', 'transit', 'how to get to Ghibli Museum from Sugamo Tokyo train', 'https://www.rome2rio.com/s/Suginami/Ghibli-Museum', 'The best way to get from Suginami to Ghibli Museum without a car is to train which takes 23 min and costs ¥120 - ¥250.', NULL, 0.6638657, '2026-03-17 18:48:44.963038+00');
INSERT INTO public.knowledge_items (id, anchor, city, category, topic, source_url, content_summary, raw_content, tavily_score, ingested_utc) VALUES
	(649, 'tokyo-ueno', 'tokyo', 'museum', 'Tokyo National Museum highlights must see exhibits 2026', 'https://sg.trip.com/moments/theme/poi-tokyo-national-museum-78881-exhibitions-990362/', '📌 Practical info: • Hours: Tue–Thu, Sun: 9:30–17:00; Fri–Sat: 9:30–20:00; closed Mondays (with exceptions)  ￼ • Tickets: ¥1,000 adult; ¥500 students; free for youth under 18 & seniors over 70; same ticket covers most special exhibitions  ￼ • Nearby: Ueno Station (~10-min walk), Ueno Park attractions, National Museum of Western Art, and Tokyo National Science Museum  ￼ Visitor feedback echoes my experience: “Absolutely worth it if you’re interested in history and historical artifacts… they have English audio guides”  ￼ Why it stood out: • Vast collection featuring national treasures and culturally significant artifacts (paintings, scrolls, armor)  ￼ ￼ • Superb English accessibility + educational resources • Beautiful exhibition spaces and tranquil gardens—easy to spend a leisurely afternoon Final thoughts: The Tokyo National Museum is an essential stop for anyone wanting a deep, well-rounded understanding of Japanese art and history.', NULL, 0.8649622, '2026-03-17 18:48:17.515848+00'),
	(650, 'tokyo-ueno', 'tokyo', 'museum', 'Tokyo National Museum highlights must see exhibits 2026', 'https://www.magical-trip.com/media/tokyo-museum-guide-2024-must-see-art-tradition-museums/', '# Tokyo Museum Guide 2026: Must-see Art & Tradition Museums. In this guide, we''ll introduce carefully selected museums and facilities where you can enjoy and learn about Japanese traditional culture during your visit to Tokyo. Tokyo, Japan''s center of politics, economy, and culture, is home to numerous museums and art galleries showcasing globally significant artworks and historically valuable collections. ### Rich in Traditional Cultural Museums and Anime Experience Facilities Unique to Tokyo. For instance, the Edo Tokyo Museum, a premier traditional cultural facility, features life-sized recreations of Japanese streetscapes from 300-400 years ago, allowing visitors to tangibly experience the lives of people from that era. ### THE NATIONAL ART CENTER (Tokyo Museum). The most distinctive feature of this Tokyo Museum is that visitors can touch most exhibits. ### Museum of Contemporary Art, Tokyo. teamLab Planets TOKYO DMM is a new type of Tokyo Museum where visitors can experience a fully immersive digital art world with their entire body.', NULL, 0.86331123, '2026-03-17 18:48:17.52351+00'),
	(652, 'tokyo-ueno', 'tokyo', 'museum', 'Tokyo National Museum highlights must see exhibits 2026', 'https://www.tokyoweekender.com/art_and_culture/must-see-tokyo-art-exhibitions-this-march/', 'Exhibitions to see in Tokyo in March 2026, including the return of Art Fair Tokyo, a major Sorayama retrospective and beyond.', NULL, 0.79293, '2026-03-17 18:48:17.526035+00'),
	(653, 'tokyo-ueno', 'tokyo', 'museum', 'Tokyo National Museum highlights must see exhibits 2026', 'https://www.tokyoartbeat.com/en/articles/-/best-exhibitions-starting-in-january-2026-en-202512', 'Best Exhibitions Starting in January 2026 ; Ukiyo-e Ojisan Festival Jan 6 (Tue) 2026-Mar 1 (Sun) 2026 ; Abstract Beauty and Soetsu Yanagi Jan 6 (', NULL, 0.66464967, '2026-03-17 18:48:17.528756+00'),
	(654, 'tokyo-ueno', 'tokyo', 'market', 'Ameyoko market Ueno hours best things to buy street food', 'https://bokksu.com/blogs/news/inside-ameyoko-tokyo-s-colorful-market-you-can-t-miss?srsltid=AfmBOopa7fRr7BKGRp-8rf0e91XDl-Wu0PW_sv-zkHsC8fLDCuEV7JMl', 'For anyone craving an authentic Ameyoko dining experience, this lively market in Tokyo''s Ueno district is a street food paradise. But Ameyoko isn''t just about Japanese flavors as this market also offers a tempting array of Chinese street food that adds even more excitement to the culinary adventure. ### The Japanese Savory Snack and Food Box. The Happy Hour Gift Bundle. ### The Japanese Savory Snack and Food Box. The Happy Hour Gift Bundle. ### The Bokksu Ramen Box. The Japanese Savory Snack and Food Box. Amid the lively atmosphere of Ameyoko''s bustling streets, the market is a haven for anyone who loves fresh food and good deals. These lesser-known stretches of Ameyoko offer a more intimate, laid-back side of the market, inviting visitors to experience a slice of everyday Tokyo far from the main crowd. Just like the bustling market’s unbeatable bargains and authentic flavors, Bokksu Boutique delivers carefully curated gift sets filled with genuine Japanese snacks and treats—straight from Japan, without ever leaving your house.', NULL, 0.8025714, '2026-03-17 18:48:23.186559+00'),
	(655, 'tokyo-ueno', 'tokyo', 'market', 'Ameyoko market Ueno hours best things to buy street food', 'https://japantravel.navitime.com/en/area/jp/guide/NTJtrv0037-en/', 'Tips for Exploring Ameya-Yokocho Market ... ・Opening Hours: Varies by shop. Most stores operate from 10:00 AM to 7:00 PM, while restaurants and bars may stay', NULL, 0.7361925, '2026-03-17 18:48:23.191971+00'),
	(656, 'tokyo-ueno', 'tokyo', 'market', 'Ameyoko market Ueno hours best things to buy street food', 'https://www.byfood.com/blog/tokyo/ameyoko-street-food-guide-ueno', '# Ameyoko Street Food Guide in Ueno. Ameya Yokocho (Ameyoko, for short) is a famous shopping street in Ueno, a Tokyo district with attractions such as the Tokyo Metropolitan Museum of Art, the Tokyo National Museum, and Ueno Park. Ameyoko is a must-visit Tokyo shopping street, providing authentic Japanese street food in Ueno that won''t break the bank. Located between Okachimachi Station and Ueno Station, the sprawling expanse of Ameyoko is home to around 400 stores which sell Japanese street food, seafood, snacks, clothing, and more. The Ameyoko Street Food Guide will cover the must-try street food gems in the area, read on to find out more about this popular Ueno food spot. This Ameyoko Street Food Guide has covered some of the most delicious eats in Ueno''s famous Ameya Yokocho shopping street. Ueno, Tokyo''s cultural center, is home to not only Ueno Park and several famous museums, but also some of the most delicious Japanese street food.', NULL, 0.70871735, '2026-03-17 18:48:23.194219+00'),
	(657, 'tokyo-ueno', 'tokyo', 'market', 'Ameyoko market Ueno hours best things to buy street food', 'https://www.magical-trip.com/media/best-street-food-at-ueno-2024-5-must-try-spots-in-ameyoko-market/', 'In Ameyoko, the most popular tour is the "**All-You-Can-Drink Bar Hopping Tour in Ueno**." The expert local guide takes you to three carefully selected spots: two recommended izakayas that only locals know about, plus one venue specifically chosen to match the guests'' preferences. In this article, we''ll introduce you to the best street food at Ueno 2026, focusing on the food stalls you can enjoy while strolling around Ueno Station and the Ameyoko area. Ueno is one of Tokyo''s top gourmet spots where you can fully enjoy food hopping and bar hopping. Food hopping and bar hopping in Ueno not only allow you to indulge in local flavors but also immerse yourself in the warm atmosphere of Tokyo''s old downtown. Ameyoko is a lively shopping street within walking distance from Ueno Station, popular for food hopping and shopping. Take a break from Japanese cuisine and savor freshly made Korean dishes while enjoying the lively atmosphere of Ueno. ## Enjoy Bar Hopping at "Ameyoko," the Symbol of Ueno!', NULL, 0.6897452, '2026-03-17 18:48:23.196298+00'),
	(658, 'tokyo-ueno', 'tokyo', 'market', 'Ameyoko market Ueno hours best things to buy street food', 'https://www.facebook.com/groups/457573074653783/posts/2209511419459931/', '❤️✅️ Ameyoko is a bustling market street in the Ueno area of Tokyo, famous for its wide variety of street food, including takoyaki. Takoyaki, a', NULL, 0.6803909, '2026-03-17 18:48:23.199164+00'),
	(677, 'ghibli-museum', 'tokyo', 'transit', 'how to get to Ghibli Museum from Sugamo Tokyo train', 'https://www.facebook.com/groups/457573074653783/posts/1750607442017000/', 'You''d have to do: Tokyo > Nagoya station > subway Higashiyama line until the very last stop which is Fujigaoka Station > monorail linimo line to', NULL, 0.6219319, '2026-03-17 18:48:44.965934+00'),
	(659, 'tokyo-ueno', 'tokyo', 'restaurant', 'best restaurants near Ueno Park Tokyo', 'https://www.tripadvisor.com/RestaurantsNear-g14134278-d320441-Ueno_Park-Uenokoen_Taito_Tokyo_Tokyo_Prefecture_Kanto.html', '1. Ueno Wagyu Yakiniku USHIHACHI Kiwami. 4.9. (164 reviews) · 2. Yakiniku Iwasaki Ueno. 4.9. (95 reviews) · 3. Premium Sake Pub Gashue. 5.0.', NULL, 0.92343384, '2026-03-17 18:48:27.989799+00'),
	(660, 'tokyo-ueno', 'tokyo', 'restaurant', 'best restaurants near Ueno Park Tokyo', 'https://s.tabelog.com/en/tokyo/A1311/', '/ Izakaya (Japanese style tavern), Sushi, Seafood. *Selected for Tabelog Tonkatsu "Tabelog 100" 2026*. Selected for Tabelog Tonkatsu "Tabelog 100" 2026. / Monjyayaki, Okonomiyaki (Japanese savory pancake), Izakaya (Japanese style tavern). *Selected for Tabelog izakaya EAST "Tabelog 100" 2025*. Selected for Tabelog izakaya EAST "Tabelog 100" 2025. / Izakaya (Japanese style tavern), Seafood, Sushi. / Izakaya (Japanese style tavern), Yakitori (Grilled chicken skewers), Chicken dishes. / Yakitori (Grilled chicken skewers), Chicken dishes, Izakaya (Japanese style tavern). / Monjyayaki, Izakaya (Japanese style tavern), Okonomiyaki (Japanese savory pancake). ### *12*Gyu no Tatsujin Asakusa Ten. For group reservations, please call us! Just a 1-minute walk from Asakusa Station and Kaminarimon. ### *13*Nihonbashi Sushi Dokoro Ninomiya Ueno Ten. Just a 1-minute walk from Ueno Station''s Shinobazu Exit, enjoy authentic sushi crafted by skilled artisans at reasonable prices. / Izakaya (Japanese style tavern), Soba (Buckwheat noodles), Japanese Cuisine. [4-minute walk from Asakusa Station] A new-style soba restaurant that refreshes both body and mind with homemade soba.', NULL, 0.81875163, '2026-03-17 18:48:27.998358+00'),
	(661, 'tokyo-ueno', 'tokyo', 'restaurant', 'best restaurants near Ueno Park Tokyo', 'https://www.klook.com/en-US/destination/p50053864-ueno-park/2-food-and-dining/', 'Discover the best restuarants Ueno Park, Japan. Get the best prices of exclusive dining and food coupons only at Klook!', NULL, 0.5806618, '2026-03-17 18:48:28.00093+00'),
	(226, 'owaricho', 'kanazawa', 'practical', 'Hotel Sanraku location tips', NULL, 'Located in Owaricho. 5 min walk to Omicho Market, 10 min to Higashi Chaya District. Central location for exploring on foot.', NULL, NULL, '2026-03-17 18:37:19.800224+00'),
	(662, 'tokyo-ueno', 'tokyo', 'restaurant', 'best restaurants near Ueno Park Tokyo', 'https://www.youtube.com/watch?v=D1XJulzhfoc', 'Alsace Lorraine · Isen · Asakusa Imahan · VOLO Coffee & Tea · Hanakagura Pandayaki · Usagiya · Beard Papa · Sanrio Gift Gate Ueno.', NULL, 0.5798055, '2026-03-17 18:48:28.003389+00'),
	(663, 'tokyo-ueno', 'tokyo', 'restaurant', 'best restaurants near Ueno Park Tokyo', 'https://www.facebook.com/lesliekohzm/videos/looking-for-budget-friendly-and-delicious-eats-in-ueno-here-are-3-spots-id-recom/1409727176664210/', 'Looking for budget-friendly AND delicious eats in Ueno? Here are 3 spots I''d recommend! 1️⃣ Hakata Ramen Ichiban (博多豚骨らぁ麺 一絆 上野御徒', NULL, 0.57236487, '2026-03-17 18:48:28.006358+00'),
	(664, 'tokyo-ueno', 'tokyo', 'sakura', 'Ueno Park cherry blossom 2026 sakura forecast bloom', 'https://www.byfood.com/blog/ueno-park-sakura-p-876', '# Ueno Park Sakura 2026: A Comprehensive Guide to Tokyo’s Most Energetic Cherry Blossom Festival. This guide outlines what to expect during the season, including typical bloom timing in late March, the layout of key viewing areas, details about the evening lantern illuminations, the concentration of seasonal food stalls, and practical strategies for navigating heavy crowds. Compared to quieter blossom locations, Ueno Park is defined by high foot traffic, active picnic culture, and extended nighttime viewing, making it one of the most energetic hanami experiences in the capital. Despite the crowds, the 2026 Ueno Park sakura festival remains one of the city’s most unforgettable spring experiences. For travelers seeking a classic festival atmosphere in the heart of the capital, Ueno Park during the sakura season offers an experience that feels both traditional and thrilling. It is best to arrive before 9:00 AM to secure a picnic spot along the main avenue during sakura season at Ueno Park. Yes. During peak sakura season, more than 50 food stalls operate throughout Ueno Park in Tokyo.', NULL, 0.8687491, '2026-03-17 18:48:35.212372+00'),
	(665, 'tokyo-ueno', 'tokyo', 'sakura', 'Ueno Park cherry blossom 2026 sakura forecast bloom', 'https://sakura.weathermap.jp/en.php', '[Cherry Blossom Forecast 2026](https://sakura.weathermap.jp/en.php). ![Image 1](https://sakura.weathermap.jp/images/map_midashi.jpg)All of Japan. ![Image 2: CHERRY BLOSSOM FORECAST](https://sakura.weathermap.jp/images/sakura_front_800x450.png?2026020815). ![Image 3: CHERRY BLOSSOM FORECAST](https://sakura.weathermap.jp/images/sakura_front_title_en.png)[![Image 4: 札幌](https://sakura.weathermap.jp/images/citynames/Sapporo_en.png) 4/25](https://sakura.weathermap.jp/en.php#content_bottom_box)[![Image 5: 仙台](https://sakura.weathermap.jp/images/citynames/Sendai_en.png) 4/4](https://sakura.weathermap.jp/en.php#content_bottom_box)[![Image 6: 新潟](https://sakura.weathermap.jp/images/citynames/Niigata_en.png) 4/6](https://sakura.weathermap.jp/en.php#content_bottom_box)[![Image 7: 東京](https://sakura.weathermap.jp/images/citynames/Tokyo_en.png) 3/19](https://sakura.weathermap.jp/en.php#content_bottom_box)[![Image 8: 名古屋](https://sakura.weathermap.jp/images/citynames/Nagoya_en.png) 3/25](https://sakura.weathermap.jp/en.php#content_bottom_box)[![Image 9: 大阪](https://sakura.weathermap.jp/images/citynames/Osaka_en.png) 3/26](https://sakura.weathermap.jp/en.php#content_bottom_box)[![Image 10: 福岡](https://sakura.weathermap.jp/images/citynames/Fukuoka_en.png) 3/20](https://sakura.weathermap.jp/en.php#content_bottom_box). ![Image 11: Forecast Comment](https://sakura.weathermap.jp/images/hitokuchi_midashi_en.gif). In northern Japan, temperatures are forecast to remain higher than average through April, so earlier-than-usual flowering is expected; however, at present, it does not appear likely to be as markedly early as has been seen in many recent years. ![Image 12: First bloom / Full bloom Forecast](https://sakura.weathermap.jp/images/yosou_midashi_en.jpg). ◆Hokkaido (Wakkanai, Asahikawa, Abashiri, Obihiro, Kushiro) has a different species of cherry blossom trees - Ezoyamazakuara. ![Image 13: About WeatherMap Cherry Blossom Forecast](https://sakura.weathermap.jp/images/about_midashi_en.jpg). The forecast is based on the bloom timeline of **the official observation trees** that are located at the 58 Japan Meteorological Agency offices across the country. The forecast is based on the bloom timeline of the official observation tree.', NULL, 0.83932644, '2026-03-17 18:48:35.220791+00'),
	(666, 'tokyo-ueno', 'tokyo', 'sakura', 'Ueno Park cherry blossom 2026 sakura forecast bloom', 'https://tokyocheapo.com/living/tokyo-cherry-blossom-forecast/', '2026 Tokyo Cherry Blossom Dates — Updated. # 2026 Tokyo Cherry Blossom Dates — Updated. Don’t miss a single petal this spring: here is the latest 2026 Tokyo cherry blossom season forecast — updated March 13, 2026. ## 2026 cherry blossom dates for Tokyo and surrounding prefectures. ## Where to see cherry blossoms in Tokyo in 2026. No way — we’ve also got a list of the best Tokyo cherry blossom viewing spots, which includes less-crowded options. If you’re just missing official sakura season, fret not, there are late-blooming cherry blossoms all around Tokyo as well. ## Cherry blossom season in Japan: Average bloom dates. ## Cherry blossom FAQs. tokyo cherry blossom sakura ueno park. ### When is cherry blossom season in Tokyo? In 2026, the cherry blossom dates are expected to start on March 19th and peak on March 27th, which is a few days earlier than average. Tokyo’s cherry blossoms bloom for 2 weeks in March-April — here''s what to expect.', NULL, 0.82117355, '2026-03-17 18:48:35.229641+00'),
	(667, 'tokyo-ueno', 'tokyo', 'sakura', 'Ueno Park cherry blossom 2026 sakura forecast bloom', 'https://www.timeout.com/tokyo/news/heres-the-first-official-japan-cherry-blossom-forecast-for-2026-121925', '# Here''s the official Japan cherry blossom forecast for 2026 – updated Mar 5. Get an idea of when to expect this year’s blooms across Japan with this long-term forecast. On March 5, the Japan Meteorological Corporation released its seventh cherry blossom forecast of 2026, giving us a good idea of when sakura season is expected to begin. The JMC forecast predicts the first flowering and full bloom dates of the popular *somei yoshino* variety of cherry blossoms for around 1,000 destinations across Japan. Due to the recent warm weather in **Tokyo**, the forecast has shifted a few days earlier with cherry blossoms now predicted to start flowering on March 19, with full bloom expected around March 28. In the meantime, you can enjoy the early blooming plum and winter cherry blossoms around Tokyo. **More from Time Out Tokyo**. Sign up to our newsletter for the latest updates from Tokyo and Japan.*.', NULL, 0.77405477, '2026-03-17 18:48:35.232982+00');


--
-- Data for Name: trip_itinerary; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.trip_itinerary (id, leg_sequence, leg_type, date_local, city, title, address_en, address_ja, contact_phone, confirmation_number, notes_en, notes_ja, start_time, end_time, created_utc) VALUES
	(1, 1, 'flight', '2026-03-23', 'San Francisco', 'JL7555 SFO → LAX', 'San Francisco International Airport', 'サンフランシスコ国際空港', NULL, 'APGNWZ', 'Japan Airlines codeshare SFO→LAX connector. Connects to JL69 at Tom Bradley International Terminal (LAX).', NULL, NULL, NULL, '2026-03-15 22:44:16.595033+00'),
	(3, 3, 'accommodation', '2026-03-24', 'Osaka', 'Tenjinbashi Queen Airbnb — check in', '10-12 Namihana-cho, Kita-ku, Osaka 530-0022', '大阪市北区浪花町10-12 530-0022', NULL, NULL, 'Airbnb host: Mayu (contact via Airbnb app). Tenjinbashisuji-Rokuchome area. Nearest station: Tenjinbashisuji-Rokuchome on Osaka Metro Sakaisujisen/Tanimachi line. Supermarket and 7-Eleven within 2 min walk.', NULL, NULL, NULL, '2026-03-15 22:44:16.595033+00'),
	(5, 5, 'activity', '2026-03-26', 'Osaka', 'Universal Studios Japan (USJ) — Nintendo World', '2-1-33 Sakurajima, Konohana-ku, Osaka 554-0031', '大阪市此花区桜島2-1-33 554-0031', NULL, NULL, 'DEPART AIRBNB 5:30AM to arrive gates ~6:30am. Route: Tenjinbashisuji-Rokuchome → Osaka Metro Sakaisujisen → Osaka Station → JR Osaka Loop Line → Nishikujo → JR Yumesaki Line → Universal City Station. Nintendo World (Todd + Madeline) is the primary target — express pass highly recommended.', NULL, '05:30:00', NULL, '2026-03-15 22:44:16.595033+00'),
	(6, 6, 'transit', '2026-03-30', 'Osaka', 'Check out Tenjinbashi Queen → depart for Kanazawa', NULL, NULL, NULL, NULL, 'Check out Tenjinbashi Queen Airbnb. Travel to Kanazawa by Thunderbird limited express (Osaka Umeda → Kanazawa, ~2h30m). Depart from Osaka Umeda station.', NULL, NULL, NULL, '2026-03-15 22:44:16.595033+00'),
	(7, 7, 'accommodation', '2026-03-30', 'Kanazawa', 'Hotel Sanraku Kanazawa — check in', '1-1-1 Owaricho, Kanazawa, Ishikawa 920-0902', '石川県金沢市尾張町1-1-1 920-0902', NULL, NULL, 'Hotel Sanraku. Central location — Omicho Market 5 min walk, Higashi Chaya 10 min walk, Kenroku-en 15 min walk.', NULL, NULL, NULL, '2026-03-15 22:44:16.595033+00'),
	(8, 8, 'transit', '2026-04-01', 'Kanazawa', 'Check out Hotel Sanraku → depart for Tokyo', NULL, NULL, NULL, NULL, 'Check out Hotel Sanraku. Travel to Tokyo — Kagayaki Shinkansen Kanazawa → Tokyo (~2.5 hours) or Thunderbird to Tsuruga + Shinkansen. Brenda has train booking details.', NULL, NULL, NULL, '2026-03-15 22:44:16.595033+00'),
	(9, 9, 'accommodation', '2026-04-01', 'Tokyo', 'Sugamo Airbnb (Toshima-ku) — check in', '4-37-6 Sugamo, Toshima-ku, Tokyo 170-0002', '東京都豊島区巣鴨4-37-6 170-0002', NULL, NULL, 'Tokyo base. Sugamo station on Yamanote Line and Mita Line. 1 stop to Ikebukuro. Jizo-dori traditional shopping street 1 min walk. Supermarket nearby.', NULL, NULL, NULL, '2026-03-15 22:44:16.595033+00'),
	(10, 10, 'activity', '2026-04-03', 'Tokyo', 'Ghibli Museum — Mitaka (TIMED ENTRY NOON)', '1-1-83 Shimorenjaku, Mitaka, Tokyo 181-0013', '東京都三鷹市下連雀1-1-83 181-0013', NULL, '7961560155', 'TIMED ENTRY: 12:00 NOON. Booking: 7961560155. DO NOT BE LATE — no late entry. Route from Sugamo: Yamanote to Shinjuku → JR Chuo Line rapid to Mitaka → 10 min walk or shuttle bus (200 yen). Allow 40 min travel. DEPART SUGAMO BY 10:45AM.', NULL, '12:00:00', NULL, '2026-03-15 22:44:16.595033+00'),
	(11, 11, 'flight', '2026-04-09', 'Tokyo', 'JL2 HND → SFO — departure 4:25pm', 'Tokyo Haneda Airport, International Terminal 3', '東京国際空港（羽田空港）国際線ターミナル', NULL, 'APGNWZ', 'Departure 4:25pm. DEPART SUGAMO BY 1:30PM. Route: Sugamo → Yamanote to Hamamatsucho → Tokyo Monorail to HND (20 min); OR Sugamo → Mita Line to Mita → Keikyu Line to HND. Allow 2.5 hours for international check-in and security.', NULL, '16:25:00', NULL, '2026-03-15 22:44:16.595033+00'),
	(14, 12, 'activity', '2026-04-02', 'Tokyo', 'Tokyo National Museum + Ueno Park + Ameyoko', '13-9 Uenokoen, Taito City, Tokyo 110-8712', '東京都台東区上野公園13-9', NULL, NULL, 'Tokyo National Museum (Ueno Park) - largest art museum in Japan, opens 9:30am. Budget 2-3 hours inside. Closed Mondays. Ueno Park is prime sakura viewing in late March/early April. Ameyoko outdoor market 5-min walk from museum: street food, cheap snacks, some vintage goods. Good full-day combination.', 'General admission 1000 yen. Ameyoko: free, cash preferred. JR Ueno station 5-min walk.', NULL, NULL, '2026-03-17 03:47:51.866425+00'),
	(15, 13, 'activity', '2026-04-04', 'Tokyo', 'Sugamo Neighbourhood - Koganji Temple + Jizo-dori Shopping Street', 'Sugamo, Toshima-ku, Tokyo', '東京都豊島区巣鴨', NULL, NULL, 'Explore our home neighbourhood in Toshima-ku. Koganji Temple (Togenuki Jizo) is a beloved local shrine on the Jizo-dori covered shopping arcade - nicknamed Grandma Harajuku for its local feel and older crowd. Morning market on the 4th of each month. Good for Japanese sweets, local pharmacy finds, and everyday Tokyo life far from tourist circuit.', 'Walk north from Sugamo station (JR Yamanote or Mita Line). Jizo-dori is a 700m arcade. Matcha ice cream at Kissako Saryo popular. Morning market is Apr 4th.', NULL, NULL, '2026-03-17 03:47:51.866425+00'),
	(16, 14, 'activity', '2026-04-05', 'Tokyo', 'Shimokitazawa Vintage Shopping', 'Shimokitazawa, Setagaya-ku, Tokyo', '東京都世田谷区下北沢', NULL, NULL, 'Shimokitazawa is Tokyo best vintage and thrift district - tight alleys packed with independent vintage shops, retro cafes, and record stores. Brenda priority. From Sugamo: JR Yamanote to Shinjuku then Odakyu to Shimokitazawa (~40 min). Best shops: Chicago, New York Joe Exchange, Flamingo, Bear Pond coffee.', 'Cash preferred at most vintage shops. Arrive by 11am on weekends. Lunch: Shirube izakaya or small cafes on side streets. Evening: live music venues in the area.', NULL, NULL, '2026-03-17 03:47:51.866425+00'),
	(17, 15, 'activity', '2026-04-06', 'Tokyo', 'Harajuku + Omotesando + Shibuya Shopping Day', 'Harajuku and Shibuya, Tokyo', '東京都渋谷区', NULL, NULL, 'Full shopping day. Start Harajuku: Takeshita-dori for youth fashion, Ura-Harajuku backstreets for boutiques. Omotesando for flagship stores (Comme des Garcons, Issey Miyake, Uniqlo flagship). Meiji Shrine 10-min walk from Harajuku station (free). End at Shibuya Crossing - view from Starbucks 2nd floor or Shibuya Sky deck.', 'Meiji Shrine: free. Shibuya Sky: 2000-2500 yen, book in advance. JR Yamanote to Harajuku (20 min from Sugamo). Don Quijote Shibuya for souvenirs (open late).', NULL, NULL, '2026-03-17 03:47:51.866425+00'),
	(2, 2, 'flight', '2026-03-23', 'Los Angeles', 'JL69 LAX → KIX (Kansai International)', 'Los Angeles International Airport, Tom Bradley International Terminal', 'ロサンゼルス国際空港', NULL, 'APGNWZ', 'Japan Airlines direct to Kansai International. PNR: APGNWZ. Arrives KIX next afternoon. From KIX to Osaka Namba by Haruka express or airport bus.', NULL, NULL, NULL, '2026-03-15 22:44:16.595033+00'),
	(4, 4, 'activity', '2026-03-25', 'Nara', 'Nara day trip — deer park, Todai-ji, Kasugataisha, Naramachi', 'Nara Park, Nara City, Nara Prefecture', '奈良公園 奈良市', NULL, NULL, 'DEPART EARLY — arrive Nara before 9am to beat tour buses. Cherry blossom peak (late March) makes this timing critical. Route: Tenjinbashisuji-Rokuchome → Osaka Metro to Namba → Kintetsu Nara Line direct (~40 min). Kasugataisha Shrine is 10 min walk from deer park and far less crowded than Todai-ji. Naramachi historic district best before 10am.', 'Bring yen for deer crackers, 200 yen per pack from vendors near Todai-ji', NULL, NULL, '2026-03-15 22:44:16.595033+00');


--
-- Data for Name: trip_pois; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.trip_pois (id, city, name_en, name_ja, category, lat, lng, address_en, address_ja, tags, crowd_notes, best_time_notes, source, created_utc) VALUES
	(1, 'osaka', 'Dotonbori', '道頓堀', 'food', 34.6686000, 135.5013000, 'Dotonbori, Chuo-ku, Osaka', '大阪市中央区道頓堀', '{group,food,crowd-warning,evening}', 'Packed after 6pm, extremely so on weekends during cherry blossom. Midday is manageable. Neon lights best at night.', '11am-1pm for lunch without long waits, or 9pm+ for late dinner. Giant Glico running man sign on Ebisubashi bridge. Group-friendly — tons of variety covering all dietary profiles.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(2, 'osaka', 'Kuromon Ichiba Market', '黒門市場', 'food', 34.6694000, 135.5066000, '2 Nipponbashi, Chuo-ku, Osaka', '大阪市中央区日本橋2丁目', '{group,food,seafood,brenda}', 'Busiest 9am-noon. Many stalls wind down or close by 3pm — it is a morning market.', 'Arrive 9am for freshest selection. Brenda: exceptional seafood on sticks and fresh fish. Group: try takoyaki, grilled scallops, uni. Most stalls ready by 9:30am.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(3, 'osaka', 'Den Den Town (Nipponbashi)', 'でんでんタウン（日本橋）', 'shopping', 34.6580000, 135.5055000, 'Nipponbashi, Naniwa-ku, Osaka', '大阪市浪速区日本橋', '{madeline,todd,anime,electronics,retro-gaming,cameras}', 'Weekends packed with domestic otaku tourists. Weekday mornings quiet. Many shops open 11am.', 'Weekday morning for easiest browsing. Osaka''s equivalent of Akihabara but more local. Animate, Mandarake, Super Potato branches here. Todd: some electronics component shops on side streets.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(4, 'osaka', 'Tenjinbashi-dori Shotengai', '天神橋筋商店街', 'shopping', 34.7121000, 135.5134000, 'Tenjinbashi, Kita-ku, Osaka', '大阪市北区天神橋', '{group,food,local,shotengai}', 'Japan''s longest covered shopping street (~2.6km). Extremely local — almost no foreign tourists. Low crowds most times.', 'Morning 10am onward. Traditional food stalls, local sweets, daily goods. Good for breakfast or a morning wander from the Tenjinbashi Airbnb.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(5, 'osaka', 'Shinsekai (Kushikatsu District)', '新世界', 'food', 34.6526000, 135.5063000, 'Shinsekai, Naniwa-ku, Osaka', '大阪市浪速区新世界', '{group,food,local}', 'Touristy but authentic. Evenings draw both locals and visitors for kushikatsu (deep-fried skewers). More relaxed than Dotonbori.', 'Dinner 6-8pm. Kushikatsu restaurants line the streets — the rule is never double-dip in the shared sauce. Also Tsutenkaku Tower for views. Group dietary note: kushikatsu offers vegetable/fish skewers for Brenda.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(6, 'osaka', 'Namba Parks / Namba area', 'なんばパークス', 'food', 34.6644000, 135.5002000, '2-10-70 Nanbanaka, Naniwa-ku, Osaka', '大阪市浪速区難波中2-10-70', '{group,food}', 'Urban mall with rooftop garden — less overwhelming than street-level Dotonbori. Good for a group meal with options for all dietary profiles.', 'Lunch or dinner. Multiple restaurant floors covering Japanese, ramen, sushi. Kintetsu Nara Line access for Nara day trip.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(7, 'nara', 'Nara Park (Deer Park)', '奈良公園', 'sightseeing', 34.6853000, 135.8427000, 'Zoshicho, Nara City, Nara 630-8212', '奈良市雑司町630-8212', '{group,sightseeing,early-morning,crowd-warning,cherry-blossom}', 'Tour buses arrive 9am-10am in waves. After 10am it is very crowded during cherry blossom peak. ~1,200 wild deer roam freely — they bow for shika senbei (deer crackers) sold at kiosks.', 'ARRIVE BEFORE 9AM. Late March = cherry blossom peak — early morning light through the blossoms with deer is exceptional. Buy deer crackers at kiosks (150 yen). Hold bag away from your body.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(8, 'nara', 'Todai-ji Temple (Great Buddha)', '東大寺（大仏）', 'sightseeing', 34.6888000, 135.8398000, '406-1 Zoshicho, Nara City, Nara', '奈良市雑司町406-1', '{group,sightseeing,early-morning,crowd-warning}', 'Opens 7:30am. World''s largest wooden building. Most tour groups arrive after 10am. Entry fee ~600 yen.', '7:30-9am. The Great Buddha (15m bronze Vairocana) is genuinely awe-inspiring. Also look for the pillar with the nostril-sized hole — fitting through it is said to grant enlightenment.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(9, 'nara', 'Kasugataisha Shrine', '春日大社', 'sightseeing', 34.6814000, 135.8449000, '160 Kasuganocho, Nara City, Nara 630-8212', '奈良市春日野町160 630-8212', '{group,sightseeing,early-morning}', 'Far fewer tourists than Todai-ji despite being equally significant. 10 min walk from the main deer area. The approach path lined with 3,000 stone lanterns is stunning.', 'Open 6am. Morning is best — lantern-lined approach through forest is atmospheric. If the lantern festival dates coincide (~Feb/Aug) it is extraordinary.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(10, 'nara', 'Naramachi Historic District', 'ならまち', 'sightseeing', 34.6795000, 135.8390000, 'Naramachi, Nara City, Nara', '奈良市ならまち', '{group,sightseeing,early-morning}', 'Almost tourist-free before 10am. Preserved Edo-period merchant townhouses (machiya). Boutique cafes and craft shops.', 'Before 10am for the streets. Most cafes open 10-11am — circle back after the deer park for a late-morning coffee and browse.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(11, 'kyoto', 'Fushimi Inari Taisha', '伏見稲荷大社', 'sightseeing', 34.9671000, 135.7727000, '68 Fukakusa Yabunouchi-cho, Fushimi-ku, Kyoto', '京都市伏見区深草藪之内町68', '{group,sightseeing,early-morning,crowd-warning}', 'Gates never close. By 9am the base torii is overrun with photographers. The upper mountain trails stay manageable even at 8am — most tourists turn back at the first shrine plateau.', 'DAWN ONLY — 6am is otherworldly. The full trail to the summit takes 2+ hours; even just the first 30 min up is incredible before crowds. Accessible: Namba → Kintetsu to Tofukuji → JR to Inari (2 min walk to gates).', 'seed', '2026-03-15 22:44:20.743069+00'),
	(12, 'kyoto', 'Arashiyama Bamboo Grove', '嵐山竹林', 'sightseeing', 35.0170000, 135.6726000, 'Sagaogurayama Tabuchiyama-cho, Ukyo-ku, Kyoto', '京都市右京区嵯峨小倉山田淵山町', '{group,sightseeing,early-morning,crowd-warning}', 'The 5-minute bamboo path is tourist-overrun by 10am. At 7am you may have it nearly to yourself.', '7am. The grove path is short (5-10 min walk) — pair with Tenryu-ji garden (opens 8:30am, 500 yen) and Okochi Sanso villa. Monkeys on the hillside at Iwatayama park nearby.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(13, 'kyoto', 'Philosopher''s Path (Tetsugaku-no-Michi)', '哲学の道', 'sightseeing', 35.0148000, 135.7944000, 'Tetsugaku no Michi, Sakyo-ku, Kyoto', '京都市左京区哲学の道', '{group,sightseeing,cherry-blossom}', 'Cherry blossom peak makes this one of Kyoto''s most photographed spots. Morning is manageable; afternoon gets crowded.', 'Morning walk during cherry blossom season. 2km canal-side path flanked by ~500 cherry trees. Leads from Nanzen-ji to Ginkaku-ji (Silver Pavilion).', 'seed', '2026-03-15 22:44:20.743069+00'),
	(14, 'kyoto', 'Gion District (Hanamikoji-dori)', '祇園（花見小路通）', 'sightseeing', 35.0038000, 135.7748000, 'Gion, Higashiyama-ku, Kyoto', '京都市東山区祇園', '{group,sightseeing,evening}', 'Midday is the worst — packed with selfie sticks. Dusk (6-8pm) is when Gion is atmospheric and most likely to spot geiko/maiko walking to appointments.', 'DUSK — 6-8pm on Hanamikoji-dori. Do NOT block geiko or maiko — it is considered very rude and there are now signs prohibiting it. Just observe from the side of the street.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(15, 'kyoto', 'Kyoto International Manga Museum', '京都国際マンガミュージアム', 'entertainment', 35.0117000, 135.7574000, '452 Kinbukicho, Nakagyo-ku, Kyoto 604-0846', '京都市中京区金吹町452 604-0846', '{madeline,anime,entertainment}', 'Rarely crowded — good rainy day option. Extensive manga library you can read in the courtyard.', 'Open 10am. Allow 2-3 hours. Madeline layer: rotating exhibitions, large manga archive (~300,000 volumes), cosplay events. Adults ~900 yen.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(16, 'sakai', 'Sakai Knife District (Sakai-higashi area)', '堺刃物のまち（堺東エリア）', 'shopping', 34.5744000, 135.4838000, 'Sakai-higashi, Sakai City, Osaka Prefecture', '大阪府堺市堺区', '{todd,knives,craft}', 'Not touristy — this is where professional chefs come to buy knives. Workshops and retail shops along the main knife street.', 'Shops open ~10am. Allow half a day minimum. Todd: Japanese kitchen knives and nail/grooming kits in local Sakai steel are the primary targets. Specialist retailers will let you handle blades. Some shops offer custom engraving.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(17, 'kanazawa', 'Kenroku-en Garden', '兼六園', 'sightseeing', 36.5626000, 136.6621000, '1 Kenrokumachi, Kanazawa, Ishikawa 920-0936', '石川県金沢市兼六町1 920-0936', '{group,sightseeing,cherry-blossom}', 'One of Japan''s three great gardens. Cherry blossoms may still be in peak late March-early April window — Kanazawa is slightly later than Osaka.', 'Opens 7am in spring (free before 8am). Pair with Kanazawa Castle Park adjacent (no extra charge). The famous Kotoji lantern on the pond is the most photographed spot.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(18, 'kanazawa', 'Higashi Chaya District', '東茶屋街', 'sightseeing', 36.5705000, 136.6638000, 'Higashiyama 1-chome, Kanazawa, Ishikawa', '石川県金沢市東山1丁目', '{group,todd,sightseeing,ceramics}', 'Less crowded than Kyoto''s equivalent geisha districts. Many Kutani ware ceramics shops on and around the main street.', 'Morning (10am open). The preserved teahouse street is walkable in 30 min. Todd: multiple dedicated Kutani ware (九谷焼) retailers — look for bold overglaze enamel painting on porcelain. Some shops allow watching craftspeople.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(19, 'kanazawa', 'Omicho Market', '近江町市場', 'food', 36.5648000, 136.6578000, '50 Kamiomicho, Kanazawa, Ishikawa 920-0906', '石川県金沢市上近江町50 920-0906', '{brenda,group,food,seafood}', 'Kanazawa is Japan Sea country — exceptional seafood quality, especially winter crab (zuwaigani) and yellowtail (buri/kanburi). Busiest 9-11am.', 'Arrive 9am. Covered market with 170+ stalls. Brenda: outstanding fish and seafood options. Restaurant stalls inside offer sushi and kaisen-don (seafood rice bowls). Fresh crab to go or at seated restaurants.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(20, 'kanazawa', '21st Century Museum of Contemporary Art', '金沢21世紀美術館', 'entertainment', 36.5620000, 136.6604000, '1-2-1 Hirosaka, Kanazawa, Ishikawa 920-8509', '石川県金沢市広坂1-2-1 920-8509', '{group,entertainment}', 'Not typically crowded. Some permanent installations have timed entry (book at desk).', 'Afternoon works well. Famous ''swimming pool'' installation by Leandro Erlich — you stand underwater looking up through glass at people standing at the bottom of a drained pool. Free to enter main areas; paid zone ~360 yen.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(21, 'tokyo', 'Sugamo Jizo-dori Shotengai', '巣鴨地蔵通り商店街', 'shopping', 35.7333000, 139.7295000, 'Sugamo, Toshima-ku, Tokyo', '東京都豊島区巣鴨', '{group,local,shotengai}', 'Known colloquially as ''harajuku for grandmas'' — almost no foreign tourists, very local. Traditional sweets and daily goods.', 'Morning from 9am. Pink daifuku mochi at Maruyama Sugamo is a local speciality. A 10-min morning stroll — the base is literally outside the Airbnb.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(22, 'tokyo', 'Ikebukuro — Animate, Pokemon Center, Jump Shop', '池袋（アニメイト、ポケモンセンター、ジャンプショップ）', 'entertainment', 35.7296000, 139.7102000, 'Ikebukuro, Toshima-ku, Tokyo', '東京都豊島区池袋', '{madeline,todd,anime,entertainment}', 'Animate flagship and Sunshine City complex are busiest on weekends. Weekday afternoon is better for browsing.', 'Madeline primary zone. 1 stop from Sugamo on Yamanote or Mita Line. Animate flagship (anime merchandise), Pokemon Center (Sunshine City B1F), Jump Shop, also Sunshine Aquarium for a break. P''Parco building for more anime retailers.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(23, 'tokyo', 'Nakano Broadway', '中野ブロードウェイ', 'shopping', 35.7084000, 139.6659000, '5-52-15 Nakano, Nakano-ku, Tokyo 164-0001', '東京都中野区中野5-52-15 164-0001', '{madeline,todd,anime,cameras,retro-gaming}', 'Less tourist-overrun than Akihabara. This is where serious collectors shop. Mandarake has multiple floors dedicated to vintage anime figures, cameras, and retro games.', 'Open 12pm-8pm. Mandarake floors 2-4 are the destination for both Todd and Madeline. Todd: vintage cameras and photo equipment on dedicated floors. Madeline: vintage anime figures and retro games. Route: Sugamo → Yamanote south → Shinjuku → JR Chuo/Sobu to Nakano (~25 min).', 'seed', '2026-03-15 22:44:20.743069+00'),
	(24, 'tokyo', 'Shimokitazawa — Vintage and Thrift District', '下北沢（古着）', 'shopping', 35.6613000, 139.6677000, 'Shimokitazawa, Setagaya-ku, Tokyo', '東京都世田谷区下北沢', '{madeline,vintage,shopping}', 'Tokyo''s indie/vintage fashion district. Very local vibe — multiple blocks of used clothing boutiques, record shops, and independent cafes. Weekends busy but manageable vs. Harajuku.', 'Afternoon — most vintage shops open 12pm-1pm. Allow 2-3 hours minimum. Madeline: primary destination for thrift/used clothing. Cat Street (parallel lane) has higher-end vintage. Route: Sugamo → Yamanote to Shibuya → Keio Inokashira Line to Shimokitazawa (~40 min).', 'seed', '2026-03-15 22:44:20.743069+00'),
	(25, 'tokyo', 'Akihabara Electric Town', '秋葉原電気街', 'shopping', 35.6984000, 139.7730000, 'Sotokanda, Chiyoda-ku, Tokyo', '東京都千代田区外神田', '{todd,madeline,electronics,anime,retro-gaming,cameras}', 'Main Chuo-dori strip is tourist-heavy. The maker electronics shops (Akizuki, Marutsu, Aitendo) are 2 blocks off the main strip — far less crowded.', 'Todd MUST-VISIT: Akizuki Denshi (秋月電子通商) and Marutsu Denki (マルツ電波) for ESP32/sensors/kits — open ~11am, weekday preferred. Aitendo nearby for modules. Madeline: Super Potato (3F/4F area, retro gaming) and Animate Akihabara. Route: Sugamo → Yamanote to Akihabara (~20 min).', 'seed', '2026-03-15 22:44:20.743069+00'),
	(26, 'tokyo', 'Harajuku Takeshita Street', '原宿竹下通り', 'shopping', 35.6703000, 139.7076000, 'Jingumae 1-chome, Shibuya-ku, Tokyo', '東京都渋谷区神宮前1丁目', '{madeline,vintage,fashion}', 'Extremely packed on weekends — nearly impassable. Weekday morning is the only manageable time. Very short street (~350m).', 'Weekday morning only. Cat Street (parallel, runs behind Omotesando) is calmer and has better quality vintage shops. Harajuku station on Yamanote. Combine with Omotesando for a broader browse.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(27, 'tokyo', 'Asakusa Senso-ji Temple', '浅草寺', 'sightseeing', 35.7148000, 139.7967000, '2-3-1 Asakusa, Taito-ku, Tokyo 111-0032', '東京都台東区浅草2-3-1 111-0032', '{group,sightseeing,early-morning,crowd-warning}', 'Tokyo''s most visited temple. 6am-8am is peaceful — the grounds never close. After 10am it becomes extremely crowded with tour groups.', 'Early morning (6am) for photos without crowds. Nakamise shopping street opens ~10am (great for souvenirs and Japanese snacks). Combine with Kappabashi-dori (cookware street, 5 min walk) — Brenda and Todd both relevant.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(28, 'tokyo', 'Ghibli Museum, Mitaka', '三鷹の森ジブリ美術館', 'entertainment', 35.6962000, 139.5703000, '1-1-83 Shimorenjaku, Mitaka, Tokyo 181-0013', '東京都三鷹市下連雀1-1-83 181-0013', '{madeline,todd,ghibli,anime,entertainment}', 'TIMED ENTRY ONLY — must buy tickets in advance. No re-entry. Booking: 7961560155 (noon Apr 3). The museum is small and magical — built by Miyazaki Hayao, every corner is designed.', 'BOOKING: 7961560155. Entry noon Apr 3. Depart Sugamo by 10:45am. Route: Yamanote to Shinjuku → JR Chuo rapid to Mitaka (20 min) → 10 min walk to museum (or shuttle bus 200 yen from south exit). The rooftop robot soldier from Castle in the Sky is real and on the roof.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(29, 'tokyo', 'Map Camera, Shinjuku', 'マップカメラ（新宿）', 'shopping', 35.6932000, 139.7031000, '1-12-2 Nishishinjuku, Shinjuku-ku, Tokyo', '東京都新宿区西新宿1-12-2', '{todd,madeline,cameras}', 'Japan''s largest used camera dealer. 5 floors — not typically crowded. Staff knowledgeable.', 'Open 11am-8pm. Todd + Madeline: vintage point-and-shoot cameras are a specialty. Near Shinjuku station west exit (5 min walk). Yodobashi Camera and Bic Camera also nearby if looking for new gear.', 'seed', '2026-03-15 22:44:20.743069+00'),
	(30, 'tokyo', 'Shibuya Crossing and Shibuya Scramble', '渋谷スクランブル交差点', 'sightseeing', 35.6595000, 139.7004000, 'Shibuya, Shibuya-ku, Tokyo', '東京都渋谷区渋谷', '{group,sightseeing}', 'Busiest intersection in the world. Best viewed from above — Mag''s Park rooftop (free) or Starbucks Reserve Roastery second floor.', 'Evening for the light show effect. Daytime is still impressive. Good transit hub for Madeline (Shibuya → Keio Inokashira to Shimokitazawa). Also Shibuya 109 for Madeline''s fashion interest.', 'seed', '2026-03-15 22:44:20.743069+00');


--
-- Data for Name: user_preferences; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.user_preferences (id, user_id, category, preference_key, preference_value, notes, created_utc) VALUES
	(1, 1, 'dietary', 'eats', 'beef', NULL, '2026-03-15 22:44:11.622494+00'),
	(2, 1, 'dietary', 'eats', 'chicken', NULL, '2026-03-15 22:44:11.622494+00'),
	(3, 1, 'dietary', 'eats', 'fish', 'some fish', '2026-03-15 22:44:11.622494+00'),
	(4, 1, 'shopping', 'interest_type', 'vintage_cameras', 'no DSLR, no large lens', '2026-03-15 22:44:11.622494+00'),
	(5, 1, 'shopping', 'interest_type', 'electronics_components', 'ESP32, maker components, Akihabara', '2026-03-15 22:44:11.622494+00'),
	(6, 1, 'shopping', 'interest_type', 'ceramics', 'Kanazawa Kutani ware primary target', '2026-03-15 22:44:11.622494+00'),
	(7, 1, 'shopping', 'interest_type', 'grooming_kit', 'local Japanese steel, Sakai', '2026-03-15 22:44:11.622494+00'),
	(8, 1, 'shopping', 'interest_type', 'vintage_anime_figures', NULL, '2026-03-15 22:44:11.622494+00');


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.users (id, telegram_user_id, display_name, full_name, notification_active, language_preference, created_utc) VALUES
	(1, 204595710, 'Todd', 'Todd Ibbotson', true, 'en', '2026-03-15 22:44:11.622494+00');


--
-- Data for Name: wishlist_items; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Name: budget_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.budget_items_id_seq', 1, true);


--
-- Name: checklist_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.checklist_items_id_seq', 15, true);


--
-- Name: knowledge_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.knowledge_items_id_seq', 804, true);


--
-- Name: trip_itinerary_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.trip_itinerary_id_seq', 17, true);


--
-- Name: trip_pois_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.trip_pois_id_seq', 30, true);


--
-- Name: user_preferences_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_preferences_id_seq', 8, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: wishlist_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.wishlist_items_id_seq', 1, true);


--
-- Name: budget_items budget_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.budget_items
    ADD CONSTRAINT budget_items_pkey PRIMARY KEY (id);


--
-- Name: checklist_items checklist_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_items
    ADD CONSTRAINT checklist_items_pkey PRIMARY KEY (id);


--
-- Name: knowledge_items knowledge_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_items
    ADD CONSTRAINT knowledge_items_pkey PRIMARY KEY (id);


--
-- Name: trip_itinerary trip_itinerary_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_itinerary
    ADD CONSTRAINT trip_itinerary_pkey PRIMARY KEY (id);


--
-- Name: trip_pois trip_pois_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trip_pois
    ADD CONSTRAINT trip_pois_pkey PRIMARY KEY (id);


--
-- Name: user_preferences user_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_telegram_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_telegram_user_id_key UNIQUE (telegram_user_id);


--
-- Name: wishlist_items wishlist_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wishlist_items
    ADD CONSTRAINT wishlist_items_pkey PRIMARY KEY (id);


--
-- Name: idx_checklist_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_checklist_category ON public.checklist_items USING btree (category);


--
-- Name: idx_checklist_packed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_checklist_packed ON public.checklist_items USING btree (packed);


--
-- Name: idx_itinerary_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itinerary_city ON public.trip_itinerary USING btree (city);


--
-- Name: idx_itinerary_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_itinerary_date ON public.trip_itinerary USING btree (date_local);


--
-- Name: idx_knowledge_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_knowledge_category ON public.knowledge_items USING btree (category);


--
-- Name: idx_knowledge_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_knowledge_city ON public.knowledge_items USING btree (city);


--
-- Name: idx_pois_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pois_category ON public.trip_pois USING btree (category);


--
-- Name: idx_pois_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pois_city ON public.trip_pois USING btree (city);


--
-- Name: idx_pois_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pois_tags ON public.trip_pois USING gin (tags);


--
-- Name: idx_user_pref_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_pref_category ON public.user_preferences USING btree (user_id, category);


--
-- Name: idx_user_pref_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_pref_user_id ON public.user_preferences USING btree (user_id);


--
-- Name: idx_wishlist_requested_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wishlist_requested_by ON public.wishlist_items USING btree (requested_by);


--
-- Name: idx_wishlist_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wishlist_status ON public.wishlist_items USING btree (status);


--
-- Name: uidx_knowledge_anchor_cat_url; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uidx_knowledge_anchor_cat_url ON public.knowledge_items USING btree (COALESCE(anchor, ''::text), COALESCE(category, ''::text), COALESCE(source_url, ''::text));


--
-- Name: uidx_knowledge_items; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uidx_knowledge_items ON public.knowledge_items USING btree (city, topic, COALESCE(source_url, ''::text));


--
-- Name: user_preferences user_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: wishlist_items wishlist_items_requested_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wishlist_items
    ADD CONSTRAINT wishlist_items_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES public.users(id);


--
-- Name: wishlist_items wishlist_items_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wishlist_items
    ADD CONSTRAINT wishlist_items_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict nEg41e7zdz4WQttDLXws43FHc1A9Ltzoxg8sKVbKzac76y1AZxLNf2UwBX4R6qV

