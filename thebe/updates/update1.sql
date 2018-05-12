use thebe;
ALTER TABLE domains ADD COLUMN registrant     varchar (255);
ALTER TABLE domains ADD COLUMN addresspost    varchar (255);
ALTER TABLE domains ADD COLUMN addressstreet  varchar (255);
ALTER TABLE domains ADD COLUMN phonenum       varchar (255);
ALTER TABLE domains ADD COLUMN email          varchar (255);

