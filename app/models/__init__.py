from app.db.database import Base

# Importación de modelos
from app.models.actividades import Actividades
from app.models.captura_periodos import CapturaPeriodos
from app.models.catalogo_fuentes_financiamiento import CatalogoFuentesFinanciamiento
from app.models.catalogo_pmd import CatalogoPMD
from app.models.catalogo_programas import CatalogoProgramas
from app.models.catalogo_unidades_administrativas import CatalogoUnidadesAdministrativas
from app.models.componentes import Componentes
from app.models.ejercicio import Ejercicio
from app.models.inter_actividades_pmd import ActividadPMD
from app.models.inter_techo_financiero import TechoFinanciero
from app.models.programacion_avance import ProgramacionAvance, TrazabilidadAvances
from app.models.programacion_evidencia import ProgramacionEvidencia
from app.models.programacion_meta import ProgramacionMeta
from app.models.usuario import Usuario, RolUsuario