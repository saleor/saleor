# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        '{{last_name}} {{company_suffix}}',
        '{{last_name}}-{{last_name}}',
        '{{company_prefix}} {{last_name}}-{{last_name}}',
        '{{company_prefix}} {{last_name}} y {{last_name}}',
        '{{company_prefix}} {{last_name}}, {{last_name}} y {{last_name}}',
        '{{last_name}}-{{last_name}} {{company_suffix}}',
        '{{last_name}}, {{last_name}} y {{last_name}}',
        '{{last_name}} y {{last_name}} {{company_suffix}}',
    )

    catch_phrase_words = (
        (
            "habilidad", "acceso", "adaptador", "algoritmo", "alianza",
            "analista", "aplicación", "enfoque", "arquitectura",
            "archivo", "inteligencia artificial", "array", "actitud",
            "medición", "gestión presupuestaria", "capacidad", "desafío",
            "circuito", "colaboración", "complejidad", "concepto",
            "conglomeración", "contingencia", "núcleo", "fidelidad",
            "base de datos", "data-warehouse", "definición", "emulación",
            "codificar", "encriptar", "extranet", "firmware",
            "flexibilidad", "focus group", "previsión", "base de trabajo",
            "función", "funcionalidad", "interfaz gráfica", "groupware",
            "interfaz gráfico de usuario", "hardware", "soporte", "jerarquía",
            "conjunto", "implementación", "infraestructura", "iniciativa",
            "instalación", "conjunto de instrucciones", "interfaz",
            "intranet", "base del conocimiento", "red de area local",
            "aprovechar", "matrices", "metodologías", "middleware",
            "migración", "modelo", "moderador", "monitorizar",
            "arquitectura abierta", "sistema abierto", "orquestar",
            "paradigma", "paralelismo", "política", "portal",
            "estructura de precios", "proceso de mejora",
            "producto", "productividad", "proyecto", "proyección",
            "protocolo", "línea segura", "software", "solución",
            "estandarización", "estrategia", "estructura", "éxito",
            "superestructura", "soporte", "sinergia", "mediante",
            "marco de tiempo", "caja de herramientas", "utilización",
            "website", "fuerza de trabajo"),
        (
            "24 horas", "24/7", "3ra generación", "4ta generación",
            "5ta generación", "6ta generación", "analizada",
            "asimétrica", "asíncrona", "monitorizada por red",
            "bidireccional", "bifurcada", "generada por el cliente",
            "cliente-servidor", "coherente", "cohesiva", "compuesto",
            "sensible al contexto", "basado en el contexto",
            "basado en contenido", "dedicada",
            "generado por la demanda", "didáctica", "direccional",
            "discreta", "dinámica", "potenciada", "acompasada",
            "ejecutiva", "explícita", "tolerante a fallos",
            "innovadora", "amplio abanico", "global", "heurística",
            "alto nivel", "holística", "homogénea", "híbrida",
            "incremental", "intangible", "interactiva", "intermedia",
            "local", "logística", "maximizada", "metódica",
            "misión crítica", "móvil", "modular", "motivadora",
            "multimedia", "multiestado", "multitarea", "nacional",
            "basado en necesidades", "neutral", "nueva generación",
            "no-volátil", "orientado a objetos", "óptima", "optimizada",
            "radical", "tiempo real", "recíproca", "regional",
            "escalable", "secundaria", "orientada a soluciones",
            "estable", "estática", "sistemática", "sistémica",
            "tangible", "terciaria", "transicional", "uniforme",
            "valor añadido", "vía web", "defectos cero", "tolerancia cero",
        ),
        (
            'adaptativo', 'avanzado', 'asimilado', 'automatizado',
            'balanceado', 'enfocado al negocio',
            'centralizado', 'clonado', 'compatible', 'configurable',
            'multiplataforma', 'enfocado al cliente', 'personalizable',
            'descentralizado', 'digitalizado', 'distribuido', 'diverso',
            'mejorado', 'en toda la empresa', 'ergonómico', 'exclusivo',
            'expandido', 'extendido', 'cara a cara', 'enfocado',
            'de primera línea', 'totalmente configurable',
            'basado en funcionalidad', 'fundamental', 'horizontal',
            'implementado', 'innovador', 'integrado', 'intuitivo',
            'inverso', 'administrado', 'mandatorio', 'monitoreado',
            'multicanal', 'multilateral', 'multi-capas', 'en red',
            'basado en objetos', 'de arquitectura abierta',
            'open-source', 'operativo', 'optimizado', 'opcional',
            'orgánico', 'organizado', 'perseverante', 'persistente',
            'polarizado', 'preventivo', 'proactivo', 'enfocado a ganancias',
            'programable', 'progresivo', 'llave pública',
            'enfocado a la calidad', 'reactivo', 'realineado',
            'recontextualizado', 'reducido', 'con ingeniería inversa',
            'de tamaño adecuado', 'robusto', 'seguro', 'compartible',
            'sincronizado', 'orientado a equipos', 'total',
            'universal', 'actualizable', 'centrado en el usuario',
            'versátil', 'virtual', 'visionario',
        ),
    )

    bsWords = (
        (
            'implementa', 'utiliza', 'integra', 'optimiza',
            'evoluciona', 'transforma', 'abraza', 'habilita',
            'orquesta', 'reinventa', 'agrega', 'mejora', 'incentiva',
            'modifica', 'empodera', 'monetiza', 'fortalece',
            'facilita', 'sinergiza', 'crea marca', 'crece',
            'sintetiza', 'entrega', 'mezcla', 'incuba', 'compromete',
            'maximiza', 'visualiza', 'innova',
            'escala', 'libera', 'maneja', 'extiende', 'revoluciona',
            'genera', 'explota', 'transiciona', 'itera', 'cultiva',
            'redefine', 'recontextualiza',
        ),
        (
            'sinergias', 'paradigmas', 'marcados', 'socios',
            'infraestructuras', 'plataformas', 'iniciativas',
            'canales', 'communidades', 'ROI', 'soluciones',
            'portales', 'nichos', 'tecnologías', 'contenido',
            'cadena de producción', 'convergencia', 'relaciones',
            'arquitecturas', 'interfaces', 'comercio electrónico',
            'sistemas', 'ancho de banda', 'modelos', 'entregables',
            'usuarios', 'esquemas', 'redes', 'aplicaciones', 'métricas',
            'funcionalidades', 'experiencias', 'servicios web',
            'metodologías',
        ),
        (
            'valor agregado', 'verticales', 'proactivas', 'robustas',
            'revolucionarias', 'escalables', 'de punta', 'innovadoras',
            'intuitivas', 'estratégicas', 'e-business', 'de misión crítica',
            'uno-a-uno', '24/7', 'end-to-end', 'globales', 'B2B', 'B2C',
            'granulares', 'sin fricciones', 'virtuales', 'virales',
            'dinámicas', '24/365', 'magnéticas', 'listo para la web',
            'interactivas', 'punto-com', 'sexi', 'en tiempo real',
            'eficientes', 'front-end', 'distribuidas', 'extensibles',
            'llave en mano', 'de clase mundial', 'open-source',
            'plataforma cruzada', 'de paquete', 'empresariales',
            'integrado', 'impacto total', 'inalámbrica', 'transparentes',
            'de siguiente generación', 'lo último', 'centrado al usuario',
            'visionarias', 'personalizado', 'ubicuas', 'plug-and-play',
            'colaborativas', 'holísticas', 'ricas',
        ),
    )

    company_preffixes = ('Despacho', 'Grupo', 'Corporacin', 'Club',
                         'Industrias', 'Laboratorios', 'Proyectos')

    company_suffixes = ('A.C.', 'S.A.', 'S.A. de C.V.', 'S.C.',
                        'S. R.L. de C.V.', 'e Hijos', 'y Asociados')

    def company_prefix(self):
        """
        Ejemplo: Grupo
        """
        return self.random_element(self.company_preffixes)

    def catch_phrase(self):
        """
        :example 'Robust full-range hub'
        """
        result = []
        for word_list in self.catch_phrase_words:
            result.append(self.random_element(word_list))

        return " ".join(result)

    def bs(self):
        """
        :example 'integrate extensible convergence'
        """
        result = []
        for word_list in self.bsWords:
            result.append(self.random_element(word_list))

        return " ".join(result)
