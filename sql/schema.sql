DROP TABLE IF EXISTS product CASCADE;
DROP TABLE IF EXISTS usr CASCADE;
DROP TABLE IF EXISTS "order" CASCADE;
DROP TABLE IF EXISTS order_products;
DROP TABLE IF EXISTS "category" CASCADE;
DROP TABLE IF EXISTS category_products;
DROP TABLE IF EXISTS "feature" CASCADE;
DROP TABLE IF EXISTS feature_products;
DROP TABLE IF EXISTS usr_fav_products;
DROP TABLE IF EXISTS blocked_jwt;

CREATE TABLE usr (
  id SERIAL PRIMARY KEY NOT NULL,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role varchar(20)
);

CREATE TABLE product (
  id SERIAL PRIMARY KEY NOT NULL,
  title varchar(64) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  description TEXT NOT NULL
);

CREATE TABLE usr_fav_products (
    id SERIAL PRIMARY KEY NOT NULL,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) references usr (id),
    FOREIGN KEY(product_id) references product(id)
);

CREATE TABLE "order" (
    id SERIAL PRIMARY KEY NOT NULL,
    user_id INTEGER NOT NULL,
    cost MONEY NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) references usr (id)
);

CREATE TABLE order_products (
    id SERIAL PRIMARY KEY NOT NULL,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (order_id) references "order" (id),
    FOREIGN KEY(product_id) references product(id)
);

CREATE TABLE "category" (
    id SERIAL PRIMARY KEY NOT NULL,
    name varchar unique
);


CREATE TABLE category_products (
    id SERIAL PRIMARY KEY NOT NULL,
    category_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    FOREIGN KEY (category_id) references category (id),
    FOREIGN KEY(product_id) references product(id)
);

CREATE TABLE "feature" (
    id SERIAL PRIMARY KEY NOT NULL,
    name varchar,
    value varchar,
    CONSTRAINT uk_01 UNIQUE(name, value)
);


CREATE TABLE feature_products (
    id SERIAL PRIMARY KEY NOT NULL,
    feature_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    FOREIGN KEY (feature_id) references feature (id),
    FOREIGN KEY(product_id) references product(id)
);

CREATE TABLE blocked_jwt (
    id SERIAL PRIMARY KEY NOT NULL,
    jti UUID UNIQUE NOT NULL,
    created_at DATE NOT NULL
);

SELECT version();
