# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as AddressProvider


class Provider(AddressProvider):
    city_suffixes = (
        'do Sul',
        'do Norte',
        'de Minas',
        'do Campo',
        'Grande',
        'da Serra',
        'do Oeste',
        'de Goiás',
        'Paulista',
        'da Mata',
        'Alegre',
        'da Praia',
        'das Flores',
        'das Pedras',
        'dos Dourados',
        'do Amparo',
        'do Galho',
        'da Prata',
        'Verde')
    street_prefixes = (
        'Aeroporto',
        'Alameda',
        'Área',
        'Avenida',
        'Campo',
        'Chácara',
        'Colônia',
        'Condomínio',
        'Conjunto',
        'Distrito',
        'Esplanada',
        'Estação',
        'Estrada',
        'Favela',
        'Fazenda',
        'Feira',
        'Jardim',
        'Ladeira',
        'Lago',
        'Lagoa',
        'Largo',
        'Loteamento',
        'Morro',
        'Núcleo',
        'Parque',
        'Passarela',
        'Pátio',
        'Praça',
        'Quadra',
        'Recanto',
        'Residencial',
        'Rodovia',
        'Rua',
        'Setor',
        'Sítio',
        'Travessa',
        'Trecho',
        'Trevo',
        'Vale',
        'Vereda',
        'Via',
        'Viaduto',
        'Viela',
        'Vila')
    city_formats = (
        '{{last_name}}',
        '{{last_name}}',
        '{{last_name}}',
        '{{last_name}}',
        '{{last_name}} {{city_suffix}}',
        '{{last_name}} {{city_suffix}}',
        '{{last_name}} {{city_suffix}}',
        '{{last_name}} de {{last_name}}',
    )
    street_name_formats = (
        '{{street_prefix}} {{last_name}}',
        '{{street_prefix}} {{first_name}} {{last_name}}',
        '{{street_prefix}} de {{last_name}}',
    )

    street_address_formats = (
        '{{street_name}}',
        '{{street_name}}, {{building_number}}',
        '{{street_name}}, {{building_number}}',
        '{{street_name}}, {{building_number}}',
        '{{street_name}}, {{building_number}}',
        '{{street_name}}, {{building_number}}',
        '{{street_name}}, {{building_number}}',
    )

    address_formats = (
        "{{street_address}}\n{{bairro}}\n{{postcode}} {{city}} / {{estado_sigla}}", )

    building_number_formats = ('%', '%#', '%#', '%#', '%##')

    postcode_formats = ('########', '#####-###')

    bairros = (
        'Aarão Reis', 'Acaba Mundo', 'Acaiaca', 'Ademar Maldonado', 'Aeroporto', 'Aguas Claras', 'Alípio De Melo',
        'Alpes',
        'Alta Tensão 1ª Seção', 'Alta Tensão 2ª Seção', 'Alto Caiçaras', 'Alto Das Antenas', 'Alto Dos Pinheiros',
        'Alto Vera Cruz',
        'Álvaro Camargos', 'Ambrosina', 'Andiroba', 'Antonio Ribeiro De Abreu 1ª Seção', 'Aparecida 7ª Seção', 'Ápia',
        'Apolonia', 'Araguaia', 'Atila De Paiva', 'Bacurau', 'Bairro Das Indústrias Ii', 'Baleia',
        'Barão Homem De Melo 1ª Seção', 'Barão Homem De Melo 2ª Seção', 'Barão Homem De Melo 3ª Seção',
        'Barreiro', 'Beija Flor', 'Beira Linha', 'Bela Vitoria', 'Belmonte', 'Bernadete', 'Betânia', 'Biquinhas',
        'Boa Esperança', 'Boa União 1ª Seção', 'Boa União 2ª Seção', 'Boa Viagem', 'Boa Vista', 'Bom Jesus', 'Bonfim',
        'Bonsucesso', 'Brasil Industrial', 'Braúnas', 'Buraco Quente', 'Cabana Do Pai Tomás',
        'Cachoeirinha', 'Caetano Furquim', 'Caiçara - Adelaide', 'Calafate', 'Califórnia', 'Camargos', 'Campo Alegre',
        'Camponesa 1ª Seção', 'Camponesa 2ª Seção', 'Canaa', 'Canadá', 'Candelaria', 'Capitão Eduardo', 'Cardoso',
        'Casa Branca', 'Castanheira', 'Cdi Jatoba', 'Cenaculo', 'Céu Azul', 'Chácara Leonina',
        'Cidade Jardim Taquaril', 'Cinquentenário', 'Colégio Batista', 'Comiteco', 'Concórdia',
        'Cônego Pinheiro 1ª Seção',
        'Cônego Pinheiro 2ª Seção', 'Confisco', 'Conjunto Bonsucesso', 'Conjunto Califórnia I',
        'Conjunto Califórnia Ii',
        'Conjunto Capitão Eduardo', 'Conjunto Celso Machado', 'Conjunto Floramar',
        'Conjunto Jardim Filadélfia', 'Conjunto Jatoba', 'Conjunto Lagoa', 'Conjunto Minas Caixa',
        'Conjunto Novo Dom Bosco', 'Conjunto Paulo Vi', 'Conjunto Providencia', 'Conjunto Santa Maria',
        'Conjunto São Francisco De Assis', 'Conjunto Serra Verde', 'Conjunto Taquaril', 'Copacabana', 'Coqueiros',
        'Corumbiara',
        'Custodinha', 'Das Industrias I', 'Delta', 'Diamante', 'Distrito Industrial Do Jatoba', 'Dom Bosco',
        'Dom Cabral',
        'Dom Joaquim', 'Dom Silverio', 'Dona Clara', 'Embaúbas', 'Engenho Nogueira', 'Ermelinda', 'Ernesto Nascimento',
        'Esperança', 'Estrela', 'Estrela Do Oriente', 'Etelvina Carneiro', 'Europa',
        'Eymard', 'Fazendinha', 'Flamengo', 'Flavio De Oliveira', 'Flavio Marques Lisboa', 'Floramar', 'Frei Leopoldo',
        'Gameleira', 'Garças', 'Glória', 'Goiania', 'Graça', 'Granja De Freitas', 'Granja Werneck', 'Grota', 'Grotinha',
        'Guarani', 'Guaratã', 'Havaí', 'Heliopolis', 'Horto Florestal', 'Inconfidência',
        'Indaiá', 'Independência', 'Ipe', 'Itapoa', 'Itatiaia', 'Jaqueline', 'Jaraguá', 'Jardim Alvorada',
        'Jardim Atlântico', 'Jardim Do Vale', 'Jardim Dos Comerciarios', 'Jardim Felicidade', 'Jardim Guanabara',
        'Jardim Leblon', 'Jardim Montanhês', 'Jardim São José', 'Jardim Vitoria', 'Jardinópolis', 'Jatobá',
        'João Alfredo', 'João Paulo Ii', 'Jonas Veiga', 'Juliana', 'Lagoa', 'Lagoinha', 'Lagoinha Leblon', 'Lajedo',
        'Laranjeiras', 'Leonina', 'Leticia', 'Liberdade', 'Lindéia', 'Lorena', 'Madre Gertrudes', 'Madri',
        'Mala E Cuia',
        'Manacas', 'Mangueiras', 'Mantiqueira', 'Marajó', 'Maravilha', 'Marçola', 'Maria Goretti',
        'Maria Helena', 'Maria Tereza', 'Maria Virgínia', 'Mariano De Abreu', 'Marieta 1ª Seção', 'Marieta 2ª Seção',
        'Marieta 3ª Seção', 'Marilandia', 'Mariquinhas', 'Marmiteiros', 'Milionario', 'Minas Brasil', 'Minas Caixa',
        'Minaslandia', 'Mineirão', 'Miramar', 'Mirante', 'Mirtes', 'Monsenhor Messias', 'Monte Azul',
        'Monte São José', 'Morro Dos Macacos', 'Nazare', 'Nossa Senhora Aparecida', 'Nossa Senhora Da Aparecida',
        'Nossa Senhora Da Conceição', 'Nossa Senhora De Fátima', 'Nossa Senhora Do Rosário', 'Nova America',
        'Nova Cachoeirinha', 'Nova Cintra', 'Nova Esperança', 'Nova Floresta', 'Nova Gameleira', 'Nova Pampulha',
        'Novo Aarão Reis', 'Novo Das Industrias', 'Novo Glória', 'Novo Santa Cecilia', 'Novo Tupi', 'Oeste', 'Olaria',
        "Olhos D'água", 'Ouro Minas', 'Pantanal', 'Paquetá', 'Paraíso', 'Parque São José', 'Parque São Pedro',
        'Paulo Vi',
        'Pedreira Padro Lopes', 'Penha', 'Petropolis', 'Pilar', 'Pindorama', 'Pindura Saia',
        'Piraja', 'Piratininga', 'Pirineus', 'Pompéia', 'Pongelupe', 'Pousada Santo Antonio', 'Primeiro De Maio',
        'Providencia', 'Ribeiro De Abreu', 'Rio Branco', 'Salgado Filho', 'Santa Amelia', 'Santa Branca',
        'Santa Cecilia',
        'Santa Cruz', 'Santa Helena', 'Santa Inês', 'Santa Isabel', 'Santa Margarida', 'Santa Maria',
        'Santa Rita', 'Santa Rita De Cássia', 'Santa Sofia', 'Santa Terezinha', 'Santana Do Cafezal', 'Santo André',
        'São Benedito', 'São Bernardo', 'São Cristóvão', 'São Damião', 'São Francisco', 'São Francisco Das Chagas',
        'São Gabriel', 'São Geraldo', 'São Gonçalo', 'São João', 'São João Batista', 'São Jorge 1ª Seção',
        'São Jorge 2ª Seção', 'São Jorge 3ª Seção', 'São José', 'São Marcos', 'São Paulo', 'São Salvador',
        'São Sebastião',
        'São Tomaz', 'São Vicente', 'Satelite', 'Saudade', 'Senhor Dos Passos', 'Serra Do Curral', 'Serra Verde',
        'Serrano',
        'Solar Do Barreiro', 'Solimoes', 'Sport Club', 'Suzana', 'Taquaril',
        'Teixeira Dias', 'Tiradentes', 'Tirol', 'Tres Marias', 'Trevo', 'Túnel De Ibirité', 'Tupi A', 'Tupi B', 'União',
        'Unidas', 'Universitário', 'Universo', 'Urca', 'Vale Do Jatoba', 'Varzea Da Palma', 'Venda Nova', 'Ventosa',
        'Vera Cruz', 'Vila Aeroporto', 'Vila Aeroporto Jaraguá', 'Vila Antena', 'Vila Antena Montanhês',
        'Vila Atila De Paiva', 'Vila Bandeirantes', 'Vila Barragem Santa Lúcia', 'Vila Batik', 'Vila Betânia',
        'Vila Boa Vista', 'Vila Calafate', 'Vila Califórnia', 'Vila Canto Do Sabiá', 'Vila Cemig', 'Vila Cloris',
        'Vila Copacabana', 'Vila Copasa', 'Vila Coqueiral', 'Vila Da Amizade', 'Vila Da Ária', 'Vila Da Luz',
        'Vila Da Paz', 'Vila Das Oliveiras', 'Vila Do Pombal', 'Vila Dos Anjos', 'Vila Ecológica',
        'Vila Engenho Nogueira',
        'Vila Esplanada', 'Vila Formosa', 'Vila Fumec', 'Vila Havaí', 'Vila Independencia 1ª Seção',
        'Vila Independencia 2ª Seção', 'Vila Independencia 3ª Seção', 'Vila Inestan', 'Vila Ipiranga',
        'Vila Jardim Alvorada', 'Vila Jardim Leblon', 'Vila Jardim São José', 'Vila Madre Gertrudes 1ª Seção',
        'Vila Madre Gertrudes 2ª Seção', 'Vila Madre Gertrudes 3ª Seção', 'Vila Madre Gertrudes 4ª Seção',
        'Vila Maloca',
        'Vila Mangueiras', 'Vila Mantiqueira', 'Vila Maria', 'Vila Minaslandia', 'Vila Nossa Senhora Do Rosário',
        'Vila Nova', 'Vila Nova Cachoeirinha 1ª Seção', 'Vila Nova Cachoeirinha 2ª Seção',
        'Vila Nova Cachoeirinha 3ª Seção', 'Vila Nova Dos Milionarios', 'Vila Nova Gameleira 1ª Seção',
        'Vila Nova Gameleira 2ª Seção', 'Vila Nova Gameleira 3ª Seção', 'Vila Nova Paraíso', 'Vila Novo São Lucas',
        'Vila Oeste', "Vila Olhos D'água",
        'Vila Ouro Minas', 'Vila Paquetá', 'Vila Paraíso', 'Vila Petropolis', 'Vila Pilar', 'Vila Pinho',
        'Vila Piratininga', 'Vila Piratininga Venda Nova', 'Vila Primeiro De Maio', 'Vila Puc', 'Vila Real 1ª Seção',
        'Vila Real 2ª Seção', 'Vila Rica', 'Vila Santa Monica 1ª Seção', 'Vila Santa Monica 2ª Seção',
        'Vila Santa Rosa',
        'Vila Santo Antônio', 'Vila Santo Antônio Barroquinha', 'Vila São Dimas', 'Vila São Francisco',
        'Vila São Gabriel',
        'Vila São Gabriel Jacui', 'Vila São Geraldo', 'Vila São João Batista', 'Vila São Paulo', 'Vila São Rafael',
        'Vila Satélite', 'Vila Sesc', 'Vila Sumaré', 'Vila Suzana Primeira Seção', 'Vila Suzana Segunda Seção',
        'Vila Tirol', 'Vila Trinta E Um De Março', 'Vila União', 'Vila Vista Alegre', 'Virgínia', 'Vista Alegre',
        'Vista Do Sol', 'Vitoria', 'Vitoria Da Conquista', 'Xangri-Lá', 'Xodo-Marize', 'Zilah Sposito', 'Outro',
        'Novo São Lucas', 'Esplanada', 'Estoril', 'Novo Ouro Preto', 'Ouro Preto', 'Padre Eustáquio', 'Palmares',
        'Palmeiras', 'Vila De Sá', 'Floresta', 'Anchieta', 'Aparecida', 'Grajaú', 'Planalto', 'Bandeirantes',
        'Gutierrez',
        'Jardim América', 'Renascença', 'Barro Preto', 'Barroca', 'Sagrada Família', 'Ipiranga', 'Belvedere',
        'Santa Efigênia', 'Santa Lúcia', 'Santa Monica', 'Vila Jardim Montanhes', 'Santa Rosa', 'Santa Tereza',
        'Buritis', 'Vila Paris', 'Santo Agostinho', 'Santo Antônio', 'Caiçaras', 'São Bento', 'Prado', 'Lourdes',
        'Fernão Dias', 'Carlos Prates', 'Carmo', 'Luxemburgo', 'São Lucas', 'São Luiz', 'Mangabeiras', 'São Pedro',
        'Horto',
        'Cidade Jardim', 'Castelo', 'Cidade Nova', 'Savassi', 'Serra', 'Silveira', 'Sion', 'Centro',
        'Alto Barroca', 'Nova Vista', 'Coração De Jesus', 'Coração Eucarístico', 'Funcionários', 'Cruzeiro',
        'João Pinheiro', 'Nova Granada', 'Nova Suíça', 'Itaipu',
    )
    countries = (
        'Afeganistão', 'África do Sul', 'Akrotiri', 'Albânia', 'Alemanha', 'Andorra', 'Angola', 'Anguila',
        'Antártica', 'Antígua e Barbuda', 'Antilhas Holandesas', 'Arábia Saudita', 'Argélia', 'Argentina',
        'Armênia', 'Aruba', 'Ashmore and Cartier Islands', 'Austrália', 'Áustria', 'Azerbaijão', 'Bahamas',
        'Bangladesh', 'Barbados', 'Barein', 'Bélgica', 'Belize', 'Benim', 'Bermudas', 'Bielorrússia',
        'Birmânia', 'Bolívia', 'Bósnia e Herzegovina', 'Botsuana', 'Brasil', 'Brunei', 'Bulgária',
        'Burquina Faso', 'Burundi', 'Butão', 'Cabo Verde', 'Camarões', 'Camboja', 'Canadá', 'Catar',
        'Cazaquistão', 'Chade', 'Chile', 'China', 'Chipre', 'Clipperton Island', 'Colômbia', 'Comores',
        'Congo-Brazzaville', 'Congo-Kinshasa', 'Coral Sea Islands', 'Coreia do Norte', 'Coreia do Sul',
        'Costa do Marfim', 'Costa Rica', 'Croácia', 'Cuba', 'Dhekelia', 'Dinamarca', 'Domínica', 'Egito',
        'Costa do Marfim', 'Costa Rica', 'Croácia', 'Cuba', 'Dhekelia', 'Dinamarca', 'Domínica', 'Egito',
        'Emirados Árabes Unidos', 'Equador', 'Eritreia', 'Eslováquia', 'Eslovênia', 'Espanha',
        'Estados Unidos',
        'Estônia', 'Etiópia', 'Faroé', 'Fiji', 'Filipinas', 'Finlândia', 'França', 'Gabão', 'Gâmbia', 'Gana',
        'Geórgia', 'Geórgia do Sul e Sandwich do Sul', 'Gibraltar', 'Granada', 'Grécia', 'Gronelândia',
        'Guam', 'Guatemala', 'Guernsey', 'Guiana', 'Guiné', 'Guiné Equatorial', 'Guiné-Bissau', 'Haiti',
        'Honduras', 'Hong Kong', 'Hungria', 'Iêmen', 'Ilha Bouvet', 'Ilha do Natal', 'Ilha Norfolk',
        'Ilhas Caiman', 'Ilhas Cook', 'Ilhas dos Cocos', 'Ilhas Falkland', 'Ilhas Heard e McDonald',
        'Ilhas Marshall', 'Ilhas Salomão', 'Ilhas Turcas e Caicos', 'Ilhas Virgens Americanas',
        'Ilhas Virgens Britânicas', 'Índia', 'Indonésia', 'Iran', 'Iraque', 'Irlanda', 'Islândia', 'Israel',
        'Itália', 'Jamaica', 'Jan Mayen', 'Japão', 'Jersey', 'Jibuti', 'Jordânia', 'Kuwait', 'Laos', 'Lesoto',
        'Letônia', 'Líbano', 'Libéria', 'Líbia', 'Liechtenstein', 'Lituânia', 'Luxemburgo', 'Macau',
        'Macedônia',
        'Madagáscar', 'Malásia', 'Malávi', 'Maldivas', 'Mali', 'Malta', 'Man, Isle of', 'Marianas do Norte',
        'Marrocos', 'Maurícia', 'Mauritânia', 'Mayotte', 'México', 'Micronésia', 'Moçambique', 'Moldávia',
        'Mônaco', 'Mongólia', 'Monserrate', 'Montenegro', 'Namíbia', 'Nauru', 'Navassa Island', 'Nepal',
        'Nicarágua', 'Níger', 'Nigéria', 'Niue', 'Noruega', 'Nova Caledónia', 'Nova Zelândia', 'Omã',
        'Países Baixos', 'Palau', 'Panamá', 'Papua-Nova Guiné', 'Paquistão', 'Paracel Islands', 'Paraguai',
        'Peru', 'Pitcairn', 'Polinésia Francesa', 'Polônia', 'Porto Rico', 'Portugal', 'Quênia',
        'Quirguizistão',
        'Quiribáti', 'Reino Unido', 'República Centro-Africana', 'República Checa', 'República Dominicana',
        'Roménia', 'Ruanda', 'Rússia', 'Salvador', 'Samoa', 'Samoa Americana', 'Santa Helena', 'Santa Lúcia',
        'São Cristóvão e Neves', 'São Marinho', 'São Pedro e Miquelon', 'São Tomé e Príncipe',
        'São Vicente e Granadinas', 'Sara Ocidental', 'Seicheles', 'Senegal', 'Serra Leoa', 'Sérvia',
        'Singapura', 'Síria', 'Somália', 'Sri Lanka', 'Suazilândia', 'Sudão', 'Suécia', 'Suíça', 'Suriname',
        'Svalbard e Jan Mayen', 'Tailândia', 'Taiwan', 'Tajiquistão', 'Tanzânia',
        'Território Britânico do Oceano Índico',
        'Territórios Austrais Franceses', 'Timor Leste', 'Togo', 'Tokelau', 'Tonga', 'Trindade e Tobago',
        'Tunísia', 'Turquemenistão', 'Turquia', 'Tuvalu', 'Ucrânia', 'Uganda', 'União Europeia', 'Uruguai',
        'Usbequistão', 'Vanuatu', 'Vaticano', 'Venezuela', 'Vietnam', 'Wake Island', 'Wallis e Futuna',
        'Zâmbia', 'Zimbabué',
    )

    estados = (
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP',
                                            'Amapá'), ('AM', 'Amazonas'), ('BA', 'Bahia'),
        ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES',
                                                      'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'),
        ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG',
                                                              'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'),
        ('PR', 'Paraná'), ('PE', 'Pernambuco'), ('PI',
                                                 'Piauí'), ('RJ', 'Rio de Janeiro'),
        ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR',
                                                          'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'),
        ('SE', 'Sergipe'), ('TO', 'Tocantins'),
    )

    def street_prefix(self):
        """
        :example 'rua'
        """
        return self.random_element(self.street_prefixes)

    def estado(self):
        """
        Randomly returns a Brazilian State  ('sigla' , 'nome').
        :example ('MG' . 'Minas Gerais')
        """
        return self.random_element(self.estados)

    def estado_nome(self):
        """
        Randomly returns a Brazilian State Name
        :example 'Minas Gerais'
        """
        return self.estado()[1]

    def estado_sigla(self):
        """
        Randomly returns the abbreviation of a Brazilian State

        :example 'MG'
        """
        return self.estado()[0]

    def bairro(self):
        """
        Randomly returns a bairro (neighborhood) name.
        The names were taken from the city of Belo Horizonte - Minas Gerais

        :example 'Serra'
        """
        return self.random_element(self.bairros)

    # aliases
    def neighborhood(self):
        return self.bairro()

    def state(self):
        return self.estado_nome()

    def state_abbr(self):
        return self.estado_sigla()
