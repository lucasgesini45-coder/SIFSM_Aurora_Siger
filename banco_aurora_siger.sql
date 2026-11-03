
BEGIN
  FOR t IN (SELECT table_name FROM user_tables
            WHERE table_name IN ('RECOMENDACAO_IA','REGRESSAO_RESULTADO',
                                 'INTERVALO_HORARIO','SIMULACAO')) LOOP
    EXECUTE IMMEDIATE 'DROP TABLE ' || t.table_name || ' CASCADE CONSTRAINTS PURGE';
  END LOOP;
END;
/

-- ---------------------------------------------------------------------
-- 2. TABELAS
-- ---------------------------------------------------------------------

CREATE TABLE simulacao (
  id               NUMBER GENERATED ALWAYS AS IDENTITY,
  nome             VARCHAR2(100)  NOT NULL,
  data_inicio      DATE           NOT NULL,
  dias             NUMBER(2)      DEFAULT 7   NOT NULL,
  total_intervalos NUMBER(4)      DEFAULT 168 NOT NULL,
  semente          NUMBER(10)     DEFAULT 42  NOT NULL,  -- reprodutibilidade
  status           VARCHAR2(15)   DEFAULT 'CRIADA' NOT NULL,
  criado_em        TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_simulacao PRIMARY KEY (id),
  CONSTRAINT uq_simulacao_nome UNIQUE (nome),
  CONSTRAINT ck_sim_dias CHECK (dias = 7),
  CONSTRAINT ck_sim_total CHECK (total_intervalos = dias * 24),
  CONSTRAINT ck_sim_status CHECK (status IN ('CRIADA','EXECUTADA','ANALISADA'))
);


CREATE TABLE intervalo_horario (
  id               NUMBER GENERATED ALWAYS AS IDENTITY,
  simulacao_id     NUMBER         NOT NULL,
  numero_intervalo NUMBER(3)      NOT NULL,   -- 1 a 168
  dia              NUMBER(1)      NOT NULL,   -- 1 a 7
  hora             NUMBER(2)      NOT NULL,   -- 0 a 23
  data_hora        TIMESTAMP      NOT NULL,
  temperatura_c    NUMBER(5,2)    NOT NULL,
  irradiancia_wm2  NUMBER(7,2)    NOT NULL,
  geracao_kwh      NUMBER(10,3)   NOT NULL,
  consumo_kwh      NUMBER(10,3)   NOT NULL,
  saldo_kwh        NUMBER(10,3) GENERATED ALWAYS AS (geracao_kwh - consumo_kwh) VIRTUAL,
  CONSTRAINT pk_intervalo PRIMARY KEY (id),
  CONSTRAINT fk_intervalo_simulacao FOREIGN KEY (simulacao_id)
    REFERENCES simulacao (id) ON DELETE CASCADE,
  CONSTRAINT uq_intervalo UNIQUE (simulacao_id, numero_intervalo),
  CONSTRAINT ck_int_numero CHECK (numero_intervalo BETWEEN 1 AND 168),
  CONSTRAINT ck_int_dia CHECK (dia BETWEEN 1 AND 7),
  CONSTRAINT ck_int_hora CHECK (hora BETWEEN 0 AND 23),
  CONSTRAINT ck_int_irrad CHECK (irradiancia_wm2 >= 0),
  CONSTRAINT ck_int_geracao CHECK (geracao_kwh >= 0),
  CONSTRAINT ck_int_consumo CHECK (consumo_kwh >= 0)
);

CREATE INDEX ix_intervalo_sim_dia ON intervalo_horario (simulacao_id, dia);


CREATE TABLE regressao_resultado (
  id               NUMBER GENERATED ALWAYS AS IDENTITY,
  simulacao_id     NUMBER         NOT NULL,
  variavel_x       VARCHAR2(50)   NOT NULL,
  variavel_y       VARCHAR2(50)   NOT NULL,
  coef_angular     NUMBER(18,6)   NOT NULL,
  intercepto       NUMBER(18,6)   NOT NULL,
  r_quadrado       NUMBER(8,6)    NOT NULL,
  n_observacoes    NUMBER(4)      NOT NULL,
  criado_em        TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_regressao PRIMARY KEY (id),
  CONSTRAINT fk_regressao_simulacao FOREIGN KEY (simulacao_id)
    REFERENCES simulacao (id) ON DELETE CASCADE,
  CONSTRAINT ck_reg_r2 CHECK (r_quadrado BETWEEN 0 AND 1),
  CONSTRAINT ck_reg_n CHECK (n_observacoes > 1)
);

CREATE INDEX ix_regressao_sim ON regressao_resultado (simulacao_id);

CREATE TABLE recomendacao_ia (
  id               NUMBER GENERATED ALWAYS AS IDENTITY,
  simulacao_id     NUMBER         NOT NULL,
  modelo           VARCHAR2(80)   NOT NULL,
  tipo             VARCHAR2(15)   NOT NULL,
  texto            CLOB           NOT NULL,
  criado_em        TIMESTAMP      DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_recomendacao PRIMARY KEY (id),
  CONSTRAINT fk_recomendacao_simulacao FOREIGN KEY (simulacao_id)
    REFERENCES simulacao (id) ON DELETE CASCADE,
  CONSTRAINT ck_rec_tipo CHECK (tipo IN ('EXPLICACAO','RECOMENDACAO','ALERTA'))
);

CREATE INDEX ix_recomendacao_sim ON recomendacao_ia (simulacao_id);

-- ---------------------------------------------------------------------
-- 3. DADOS INICIAIS PARA TESTE 
-- ---------------------------------------------------------------------
INSERT INTO simulacao (nome, data_inicio, semente)
VALUES ('Simulacao de teste', TO_DATE('2025-01-06','YYYY-MM-DD'), 42);

DECLARE
  v_sim   NUMBER;
  v_dia   NUMBER;
  v_hora  NUMBER;
  v_seno  NUMBER;
  v_irr   NUMBER;
  v_ger   NUMBER;
  v_con   NUMBER;
  v_temp  NUMBER;
  v_fator NUMBER;
  PI CONSTANT NUMBER := 3.14159265358979;
BEGIN
  SELECT id INTO v_sim FROM simulacao WHERE nome = 'Simulacao de teste';

  FOR i IN 1 .. 168 LOOP
    v_dia  := TRUNC((i - 1) / 24) + 1;
    v_hora := MOD(i - 1, 24);

    -- fator de nebulosidade que varia por dia (0,60 a 1,00)
    v_fator := 1 - MOD(v_dia * 7, 5) * 0.10;

    -- curva solar: positiva entre 6h e 18h
    IF v_hora BETWEEN 6 AND 18 THEN
      v_seno := SIN(PI * (v_hora - 6) / 12);
    ELSE
      v_seno := 0;
    END IF;

    v_irr  := ROUND(900 * v_seno * v_fator, 2);
    v_ger  := ROUND(5 * v_seno * v_fator, 3);
    v_temp := ROUND(22 + 6 * SIN(PI * (v_hora - 9) / 12), 2);

    -- consumo: base + pico noturno (18h-22h) + pequena variacao
    v_con := 2 + MOD(i, 3) * 0.1;
    IF v_hora BETWEEN 18 AND 22 THEN
      v_con := v_con + 1.5;
    END IF;
    v_con := ROUND(v_con, 3);

    INSERT INTO intervalo_horario
      (simulacao_id, numero_intervalo, dia, hora, data_hora,
       temperatura_c, irradiancia_wm2, geracao_kwh, consumo_kwh)
    VALUES
      (v_sim, i, v_dia, v_hora,
       CAST(TO_DATE('2025-01-06','YYYY-MM-DD') + (i - 1) / 24 AS TIMESTAMP),
       v_temp, v_irr, v_ger, v_con);
  END LOOP;

  UPDATE simulacao SET status = 'EXECUTADA' WHERE id = v_sim;
END;
/

INSERT INTO regressao_resultado
  (simulacao_id, variavel_x, variavel_y, coef_angular, intercepto, r_quadrado, n_observacoes)
SELECT id, 'irradiancia_wm2', 'geracao_kwh', 0.005556, 0.000000, 1.000000, 168
FROM simulacao WHERE nome = 'Simulacao de teste';

INSERT INTO recomendacao_ia (simulacao_id, modelo, tipo, texto)
SELECT id, 'modelo-local-exemplo', 'EXPLICACAO',
       'Registro de exemplo para teste. Sera substituido pelas respostas reais da IA.'
FROM simulacao WHERE nome = 'Simulacao de teste';

COMMIT;

-- ---------------------------------------------------------------------
-- 4. VALIDACAO (conferir se tudo foi criado corretamente)
-- ---------------------------------------------------------------------
-- === Tabelas criadas ===
SELECT table_name FROM user_tables
WHERE table_name IN ('SIMULACAO','INTERVALO_HORARIO','REGRESSAO_RESULTADO','RECOMENDACAO_IA')
ORDER BY table_name;

-- === Total de intervalos (esperado: 168) ===
SELECT COUNT(*) AS total_intervalos FROM intervalo_horario;

-- === Resumo por dia (7 linhas, 24 intervalos cada) ===
SELECT dia,
       COUNT(*)                  AS intervalos,
       ROUND(SUM(geracao_kwh),2) AS geracao_kwh,
       ROUND(SUM(consumo_kwh),2) AS consumo_kwh,
       ROUND(SUM(saldo_kwh),2)   AS saldo_kwh
FROM intervalo_horario
GROUP BY dia
ORDER BY dia;

-- === Constraints ===
SELECT table_name, constraint_name, constraint_type
FROM user_constraints
WHERE table_name IN ('SIMULACAO','INTERVALO_HORARIO','REGRESSAO_RESULTADO','RECOMENDACAO_IA')
  AND constraint_type IN ('P','R','U')
ORDER BY table_name, constraint_type;