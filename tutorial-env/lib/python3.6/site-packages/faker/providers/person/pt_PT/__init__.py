# coding=utf-8
from __future__ import unicode_literals
from .. import Provider as PersonProvider


class Provider(PersonProvider):
    formats = (
        '{{first_name}} {{last_name}}',
        '{{first_name}} {{last_name}}',
        '{{first_name}} {{last_name}}',
        '{{first_name}} {{last_name}}',
        '{{first_name}} {{last_name}}',
        '{{first_name}} {{last_name}}',
        '{{first_name}} {{last_name}}',
        '{{first_name}} {{prefix}} {{last_name}}',
        '{{first_name}} {{last_name}}-{{last_name}}',
        '{{first_name}}-{{first_name}} {{last_name}}',
    )

    first_names = (
        'Adriana', 'Afonso', 'Alex', 'Alexandra', 'Alexandre', 'Alice',
        'Alícia', 'Amélia', 'Ana', 'Andreia', 'André', 'Anita', 'António',
        'Ariana', 'Artur', 'Beatriz', 'Benedita', 'Benjamim', 'Bernardo',
        'Bianca', 'Brian', 'Bruna', 'Bruno', 'Bryan', 'Bárbara', 'Caetana',
        'Camila', 'Carlos', 'Carlota', 'Carminho', 'Carolina', 'Catarina',
        'Clara', 'Cláudio', 'Constança', 'Cristiano', 'César', 'Daniel',
        'Daniela', 'David', 'Denis', 'Diana', 'Diego', 'Dinis', 'Diogo',
        'Duarte', 'Débora', 'Edgar', 'Eduarda', 'Eduardo', 'Ema', 'Emanuel',
        'Emma', 'Emília', 'Enzo', 'Erica', 'Erika', 'Eva', 'Fabiana',
        'Fernando', 'Filipa', 'Filipe', 'Flor', 'Francisca', 'Francisco',
        'Frederico', 'Fábio', 'Gabriel', 'Gabriela', 'Gaspar', 'Gil', 'Gonçalo',
        'Guilherme', 'Gustavo', 'Helena', 'Henrique', 'Hugo', 'Iara', 'Igor',
        'Inês', 'Irina', 'Isaac', 'Isabel', 'Isabela', 'Ivan', 'Ivo', 'Jaime',
        'Joana', 'Joaquim', 'Joel', 'Jorge', 'José', 'João', 'Juliana',
        'Jéssica', 'Júlia', 'Kelly', 'Kevin', 'Kyara', 'Kévim', 'Lara',
        'Larissa', 'Laura', 'Leandro', 'Leonardo', 'Leonor', 'Letícia', 'Lia',
        'Lisandro', 'Lorena', 'Lourenço', 'Luana', 'Luca', 'Lucas', 'Luciana',
        'Luna', 'Luís', 'Luísa', 'Lúcia', 'Madalena', 'Mafalda', 'Manuel',
        'Mara', 'Marco', 'Marcos', 'Margarida', 'Maria', 'Mariana', 'Marta',
        'Martim', 'Mateus', 'Matias', 'Matilde', 'Mauro', 'Melissa', 'Mia',
        'Micael', 'Miguel', 'Miriam', 'Márcio', 'Mário', 'Mélanie', 'Naiara',
        'Nair', 'Nelson', 'Nicole', 'Noa', 'Noah', 'Nuno', 'Nádia', 'Núria',
        'Patrícia', 'Paulo', 'Pedro', 'Petra', 'Pilar', 'Rafael', 'Rafaela',
        'Raquel', 'Renata', 'Renato', 'Ricardo', 'Rita', 'Rodrigo', 'Rui',
        'Rúben', 'Salomé', 'Salvador', 'Samuel', 'Sandro', 'Santiago', 'Sara',
        'Sebastião', 'Simão', 'Sofia', 'Soraia', 'Sérgio', 'Tatiana', 'Teresa',
        'Tiago', 'Tomás', 'Tomé', 'Valentim', 'Valentina', 'Vasco', 'Vera',
        'Vicente', 'Victória', 'Violeta', 'Vitória', 'Vítor', 'William',
        'Wilson', 'Xavier', 'Yara', 'Yasmin', 'Álvaro', 'Ângela', 'Ângelo',
        'Érica', 'Íris',
    )

    last_names = (
        'Abreu', 'Almeida', 'Alves', 'Amaral', 'Amorim', 'Andrade', 'Anjos',
        'Antunes', 'Araújo', 'Assunção', 'Azevedo', 'Baptista', 'Barbosa',
        'Barros', 'Batista', 'Borges', 'Branco', 'Brito', 'Campos', 'Cardoso',
        'Carneiro', 'Carvalho', 'Castro', 'Coelho', 'Correia', 'Costa', 'Cruz',
        'Cunha', 'Domingues', 'Esteves', 'Faria', 'Fernandes', 'Ferreira',
        'Figueiredo', 'Fonseca', 'Freitas', 'Garcia', 'Gaspar', 'Gomes',
        'Gonçalves', 'Guerreiro', 'Henriques', 'Jesus', 'Leal', 'Leite', 'Lima',
        'Lopes', 'Loureiro', 'Lourenço', 'Macedo', 'Machado', 'Magalhães',
        'Maia', 'Marques', 'Martins', 'Matias', 'Matos', 'Melo', 'Mendes',
        'Miranda', 'Monteiro', 'Morais', 'Moreira', 'Mota', 'Moura',
        'Nascimento', 'Neto', 'Neves', 'Nogueira', 'Nunes', 'Oliveira',
        'Pacheco', 'Paiva', 'Pereira', 'Pinheiro', 'Pinho', 'Pinto', 'Pires',
        'Ramos', 'Reis', 'Ribeiro', 'Rocha', 'Rodrigues', 'Santos', 'Silva',
        'Simões', 'Soares', 'Sousa', 'Sá', 'Tavares', 'Teixeira', 'Torres',
        'Valente', 'Vaz', 'Vicente', 'Vieira',
    )

    prefixes = ('de', 'da', 'do')

    def prefix(self):
        return self.random_element(self.prefixes)
