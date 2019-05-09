# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as PersonProvider


class Provider(PersonProvider):
    formats_female = (
        '{{first_name_female}} {{last_name}}',
        '{{first_name_female}} {{last_name}}',
        '{{first_name_female}} {{last_name}}',
        '{{first_name_female}} {{last_name}}',
        '{{first_name_female}} {{last_name}}',
        '{{prefix_female}} {{first_name_female}} {{last_name}}',
    )

    formats_male = (
        '{{first_name_male}} {{last_name}}',
        '{{first_name_male}} {{last_name}}',
        '{{first_name_male}} {{last_name}}',
        '{{first_name_male}} {{last_name}}',
        '{{first_name_male}} {{last_name}}',
        '{{prefix_male}} {{first_name_male}} {{last_name}}',

    )

    formats = formats_male + formats_female

    """
    To a previous (undocumented?) list of female given names was added the 100
    most popular names in Brazil in 2014 and 2015 according to Exame magazine:
    * http://exame.abril.com.br/brasil/noticias/os-100-nomes-mais-comuns-no-brasil-em-2014
    * http://exame.abril.com.br/brasil/noticias/os-100-nomes-mais-comuns-no-brasil-em-2015
    """
    first_names_female = (
        'Agatha', 'Alana', 'Alexia', 'Alice', 'Alícia', 'Amanda',
        'Ana Beatriz', 'Ana Carolina', 'Ana Clara', 'Ana Julia', 'Ana Júlia',
        'Ana Laura', 'Ana Luiza', 'Ana Lívia', 'Ana Sophia', 'Ana Vitória',
        'Ana', 'Beatriz', 'Bianca', 'Brenda', 'Bruna', 'Bárbara', 'Camila',
        'Carolina', 'Caroline', 'Catarina', 'Cecília', 'Clara', 'Clarice',
        'Daniela', 'Eduarda', 'Elisa', 'Eloah', 'Emanuella', 'Emanuelly',
        'Emilly', 'Esther', 'Evelyn', 'Fernanda', 'Gabriela', 'Gabrielly',
        'Giovanna', 'Helena', 'Heloísa', 'Isabel', 'Isabella', 'Isabelly',
        'Isadora', 'Isis', 'Joana', 'Julia', 'Juliana', 'Júlia', 'Kamilly',
        'Lara', 'Larissa', 'Laura', 'Lavínia', 'Laís', 'Letícia', 'Lorena',
        'Luana', 'Luiza', 'Luna', 'Lívia', 'Maitê', 'Manuela', 'Marcela',
        'Maria Alice', 'Maria Cecília', 'Maria Clara', 'Maria Eduarda',
        'Maria Fernanda', 'Maria Julia', 'Maria Luiza', 'Maria Sophia',
        'Maria Vitória', 'Maria', 'Mariana', 'Mariane', 'Marina', 'Maysa',
        'Melissa', 'Milena', 'Mirella', 'Natália', 'Nicole', 'Nina', 'Olivia',
        'Pietra', 'Rafaela', 'Raquel', 'Rebeca', 'Sabrina', 'Sarah', 'Sofia',
        'Sophia', 'Sophie', 'Stella', 'Stephany', 'Valentina', 'Vitória',
        'Yasmin',
    )

    """
    To a previous (undocumented?) list of male given names was added the 100
    most popular names in Brazil in 2014 and 2015 according to this blog post:
    * http://exame.abril.com.br/brasil/noticias/os-100-nomes-mais-comuns-no-brasil-em-2014
    * http://exame.abril.com.br/brasil/noticias/os-100-nomes-mais-comuns-no-brasil-em-2015
    """
    first_names_male = (
        'Alexandre', 'André', 'Anthony', 'Antônio', 'Arthur', 'Augusto',
        'Benjamin', 'Benício', 'Bernardo', 'Breno', 'Bruno', 'Bryan', 'Caio',
        'Calebe', 'Carlos Eduardo', 'Cauã', 'Cauê', 'Daniel', 'Danilo',
        'Davi Lucas', 'Davi Lucca', 'Davi Luiz', 'Davi', 'Diego', 'Diogo',
        'Eduardo', 'Emanuel', 'Enrico', 'Enzo Gabriel', 'Enzo', 'Erick',
        'Felipe', 'Fernando', 'Francisco', 'Gabriel', 'Guilherme',
        'Gustavo Henrique', 'Gustavo', 'Heitor', 'Henrique', 'Ian', 'Igor',
        'Isaac', 'Joaquim', 'João Felipe', 'João Gabriel', 'João Guilherme',
        'João Lucas', 'João Miguel', 'João Pedro', 'João Vitor', 'João',
        'Juan', 'Kaique', 'Kevin', 'Leandro', 'Leonardo', 'Levi', 'Lorenzo',
        'Lucas Gabriel', 'Lucas', 'Lucca', 'Luigi', 'Luiz Felipe',
        'Luiz Fernando', 'Luiz Gustavo', 'Luiz Henrique', 'Luiz Miguel',
        'Luiz Otávio', 'Marcelo', 'Marcos Vinicius', 'Matheus', 'Miguel',
        'Murilo', 'Nathan', 'Nicolas', 'Noah', 'Otávio', 'Paulo',
        'Pedro Henrique', 'Pedro Lucas', 'Pedro Miguel', 'Pedro', 'Pietro',
        'Rafael', 'Raul', 'Renan', 'Rodrigo', 'Ryan', 'Samuel', 'Thales',
        'Theo', 'Thiago', 'Thomas', 'Vicente', 'Vinicius', 'Vitor Gabriel',
        'Vitor Hugo', 'Vitor', 'Yago', 'Yuri',
    )

    first_names = first_names_male + first_names_female

    """
    To a previous (undocumented?) list of family names was added the 70
    most popular family names in Brazil according to this blog post:
    * http://nomeschiques.com/os-70-sobrenomes-mais-comuns-e-famosos-do-brasil/
    """
    last_names = (
        'Almeida', 'Alves', 'Aragão', 'Araújo', 'Azevedo', 'Barbosa', 'Barros',
        'Caldeira', 'Campos', 'Cardoso', 'Cardoso', 'Carvalho', 'Castro',
        'Cavalcanti', 'Correia', 'Costa', 'Costela', 'Cunha', 'da Conceição',
        'da Costa', 'da Cruz', 'da Cunha', 'da Luz', 'da Mata', 'da Mota',
        'da Paz', 'da Rocha', 'da Rosa', 'das Neves', 'Dias', 'Duarte',
        'Farias', 'Fernandes', 'Ferreira', 'Fogaça', 'Freitas', 'Gomes',
        'Gonçalves', 'Jesus', 'Lima', 'Lopes', 'Martins', 'Melo', 'Mendes',
        'Monteiro', 'Moraes', 'Moreira', 'Moura', 'Nascimento', 'Nogueira',
        'Novaes', 'Nunes', 'Oliveira', 'Peixoto', 'Pereira', 'Pinto', 'Pires',
        'Porto', 'Ramos', 'Rezende', 'Ribeiro', 'Rocha', 'Rodrigues', 'Sales',
        'Santos', 'Silva', 'Silveira', 'Souza', 'Teixeira', 'Viana', 'Vieira',
    )

    prefixes_female = ('Srta.', 'Sra.', 'Dra.')
    prefixes_male = ('Sr.', 'Dr.')
