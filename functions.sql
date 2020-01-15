DELIMITER //

create function DODAJ_RABAT(user_id_in DECIMAL(15), kod_in VARCHAR(10), procent_in  DECIMAL(3), data_waznosci_in date)
returns decimal(1)
begin
	declare users_num, code_num decimal(3) default 0;
	select count(*) into users_num from user where id_u = user_id_in;
	select count(*) into code_num from rabat where kod = kod_in;
	if users_num > 0 and code_num = 0 and procent_in > 0 and procent_in <= 100 then
		INSERT into rabat(kod, procent, data_waznosci, user_id_u) values(kod_in, procent_in, data_waznosci_in, user_id_in);
	else
		return 0;
	end if;
	return 1;
end;  //

DELIMITER ;


DELIMITER $$

CREATE PROCEDURE USUN_RABAT(
    IN  kod_in varchar(10),
    OUT status_out DECIMAL(1)
)
BEGIN

    DECLARE kod_count DEC(1) DEFAULT 0;

    SELECT
        count(*)
    INTO kod_count
    FROM rabat
    WHERE
        kod = kod_in;
	if kod_count = 1 then
		delete from rabat where kod = kod_in;
		set status_out = 1;
	else
		set status_out = 0;
	end if;

END$$

DELIMITER ;
