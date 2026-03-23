-- Penzi Dating Service
-- Database Migration v1
-- Initial table definitions

-- public.users definition

-- DROP TABLE public.users;

CREATE TABLE public.users (
	id serial4 NOT NULL,
	phone_number varchar(15) NOT NULL,
	"name" varchar(100) NOT NULL,
	age int4 NOT NULL,
	gender varchar(10) NOT NULL,
	county varchar(50) NOT NULL,
	town varchar(50) NOT NULL,
	education varchar(50) NULL,
	profession varchar(50) NULL,
	marital_status varchar(20) NULL,
	religion varchar(30) NULL,
	ethnicity varchar(50) NULL,
	self_description text NULL,
	registration_stage varchar(100) DEFAULT 'basic'::character varying NULL,
	created_at timestamp DEFAULT now() NULL,
	CONSTRAINT users_phone_number_key UNIQUE (phone_number),
	CONSTRAINT users_pkey PRIMARY KEY (id)
);


-- public.messages definition

-- DROP TABLE public.messages;

CREATE TABLE public.messages (
	id serial4 NOT NULL,
	sender varchar(20) NOT NULL,
	receiver varchar(20) NOT NULL,
	message text NOT NULL,
	direction varchar(10) NOT NULL,
	created_at timestamp DEFAULT now() NULL,
	CONSTRAINT messages_pkey PRIMARY KEY (id)
);