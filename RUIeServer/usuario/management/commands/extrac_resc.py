import glob
import os
from django.conf import settings
from django.core import serializers
from django.core.management.base import BaseCommand
from usuario.models import RescatePunto


class Command(BaseCommand):
    help = (
        "Exporta todos los registros del modelo RescatePunto en archivos JSON "
        "numerados (export_data_1.json, export_data_2.json, ...) divididos por bloques."
    )

    def add_arguments(self, parser):
        default_dir = os.path.join(settings.BASE_DIR, "test_files")
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=50000,
            help="Cantidad máxima de registros por cada archivo JSON (por defecto: 50000).",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default=default_dir,
            help=f"Carpeta donde se guardarán los archivos export_data_N.json (por defecto: {default_dir}).",
        )
        parser.add_argument(
            "--prefix",
            type=str,
            default="export_data",
            help="Prefijo de los archivos generados (por defecto: export_data -> export_data_1.json).",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Elimina archivos export_data_*.json previos en la carpeta destino antes de exportar.",
        )

    def handle(self, *args, **options):
        chunk_size = max(1, options["chunk_size"])
        output_dir = options["output_dir"]
        prefix = options["prefix"]

        os.makedirs(output_dir, exist_ok=True)

        if options["clean"]:
            old_files = glob.glob(os.path.join(output_dir, f"{prefix}_*.json"))
            for old_file in old_files:
                try:
                    os.remove(old_file)
                except OSError:
                    pass

        queryset = RescatePunto.objects.all().order_by("idRescate")
        total = queryset.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No existen registros en RescatePunto para exportar."))
            return

        self.stdout.write(
            self.style.NOTICE(
                f"Iniciando exportación de {total} registros de RescatePunto "
                f"(bloques de {chunk_size}) en '{output_dir}'..."
            )
        )

        file_index = 1
        exported_count = 0
        buffer = []

        for obj in queryset.iterator(chunk_size=5000):
            buffer.append(obj)
            if len(buffer) >= chunk_size:
                file_path = os.path.join(output_dir, f"{prefix}_{file_index}.json")
                self._write_chunk(buffer, file_path)
                exported_count += len(buffer)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [OK] Generado {os.path.basename(file_path)} ({len(buffer)} registros) "
                        f"[{exported_count}/{total}]"
                    )
                )
                buffer.clear()
                file_index += 1

        if buffer:
            file_path = os.path.join(output_dir, f"{prefix}_{file_index}.json")
            self._write_chunk(buffer, file_path)
            exported_count += len(buffer)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [OK] Generado {os.path.basename(file_path)} ({len(buffer)} registros) "
                    f"[{exported_count}/{total}]"
                )
            )
            buffer.clear()
        else:
            file_index -= 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Exportación completada exitosamente: {exported_count} registros en {file_index} archivo(s)."
            )
        )

    def _write_chunk(self, objects_list, file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            serializers.serialize(
                "json",
                objects_list,
                indent=2,
                use_natural_foreign_keys=False,
                stream=f,
            )
