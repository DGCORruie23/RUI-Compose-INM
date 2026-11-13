import glob
import json
import os
import re
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection, transaction
from usuario.models import RescatePunto


class Command(BaseCommand):
    help = (
        "Integra (importa/actualiza) registros de RescatePunto desde archivos "
        "export_data_1.json, export_data_2.json, ... conservando idRescate y sincronizando la secuencia."
    )

    def add_arguments(self, parser):
        default_dir = os.path.join(settings.BASE_DIR, "test_files")
        parser.add_argument(
            "--input-dir",
            type=str,
            default=default_dir,
            help=f"Carpeta donde se buscarán los archivos export_data_N.json (por defecto: {default_dir}).",
        )
        parser.add_argument(
            "--prefix",
            type=str,
            default="export_data",
            help="Prefijo de los archivos a importar (por defecto: export_data).",
        )
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Ruta a un archivo JSON específico si solo deseas integrar uno.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=2000,
            help="Tamaño del lote para operaciones masivas en base de datos (por defecto: 2000).",
        )
        parser.add_argument(
            "--ignore-pk",
            action="store_true",
            help="Ignora el idRescate original e inserta todos los registros como nuevos autoincrementales.",
        )

    def handle(self, *args, **options):
        input_dir = options["input_dir"]
        prefix = options["prefix"]
        single_file = options["file"]
        batch_size = max(100, options["batch_size"])
        ignore_pk = options["ignore_pk"]

        if single_file:
            if not os.path.isfile(single_file):
                self.stderr.write(self.style.ERROR(f"El archivo especificado no existe: {single_file}"))
                return
            files_to_process = [single_file]
        else:
            pattern = os.path.join(input_dir, f"{prefix}_*.json")
            matched_files = glob.glob(pattern)
            files_to_process = sorted(matched_files, key=self._natural_sort_key)

        if not files_to_process:
            self.stdout.write(
                self.style.WARNING(
                    f"No se encontraron archivos '{prefix}_*.json' en '{input_dir}'."
                )
            )
            return

        self.stdout.write(
            self.style.NOTICE(
                f"Se encontraron {len(files_to_process)} archivo(s) para integrar."
            )
        )

        model_fields = {
            f.name for f in RescatePunto._meta.concrete_fields if f.name != "idRescate"
        }
        update_field_names = list(model_fields)

        total_created = 0
        total_updated = 0

        for file_path in files_to_process:
            fname = os.path.basename(file_path)
            self.stdout.write(f"Procesando {fname}...")

            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if not isinstance(raw_data, list):
                self.stderr.write(
                    self.style.WARNING(f"  [OMITIDO] {fname} no contiene una lista JSON válida.")
                )
                continue

            records = []
            for item in raw_data:
                if not isinstance(item, dict):
                    continue
                # Soportar tanto formato fixture de Django ({"model": ..., "pk": ..., "fields": {...}})
                # como diccionarios planos de campos.
                if "fields" in item and isinstance(item["fields"], dict):
                    fields_data = item["fields"]
                    pk_val = item.get("pk") or fields_data.get("idRescate")
                else:
                    fields_data = item
                    pk_val = item.get("idRescate") or item.get("pk")

                clean_kwargs = {
                    k: v for k, v in fields_data.items() if k in model_fields
                }
                if not ignore_pk and pk_val is not None:
                    clean_kwargs["idRescate"] = int(pk_val)

                records.append(RescatePunto(**clean_kwargs))

            file_created = 0
            file_updated = 0

            with transaction.atomic():
                for i in range(0, len(records), batch_size):
                    batch = records[i : i + batch_size]
                    if ignore_pk:
                        RescatePunto.objects.bulk_create(batch, batch_size=batch_size)
                        file_created += len(batch)
                    else:
                        pks_in_batch = [
                            r.idRescate for r in batch if r.idRescate is not None
                        ]
                        existing_pks = set(
                            RescatePunto.objects.filter(
                                idRescate__in=pks_in_batch
                            ).values_list("idRescate", flat=True)
                        )
                        to_create = []
                        to_update = []
                        for r in batch:
                            if r.idRescate in existing_pks:
                                to_update.append(r)
                            else:
                                to_create.append(r)

                        if to_create:
                            RescatePunto.objects.bulk_create(
                                to_create, batch_size=batch_size
                            )
                            file_created += len(to_create)

                        if to_update:
                            RescatePunto.objects.bulk_update(
                                to_update,
                                fields=update_field_names,
                                batch_size=batch_size,
                            )
                            file_updated += len(to_update)

            total_created += file_created
            total_updated += file_updated
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [OK] {fname}: {file_created} nuevos insertados, {file_updated} actualizados."
                )
            )

        # Sincronizar secuencia de autoincremento en PostgreSQL (evita IntegrityError en futuros inserts)
        self._reset_postgres_sequence()

        self.stdout.write(
            self.style.SUCCESS(
                f"Integración finalizada: {total_created} insertados, {total_updated} actualizados en total."
            )
        )

    def _natural_sort_key(self, path):
        basename = os.path.basename(path)
        return [
            int(text) if text.isdigit() else text.lower()
            for text in re.split(r"(\d+)", basename)
        ]

    def _reset_postgres_sequence(self):
        sequence_sql = connection.ops.sequence_reset_sql(no_style(), [RescatePunto])
        if sequence_sql:
            with connection.cursor() as cursor:
                for sql in sequence_sql:
                    cursor.execute(sql)
            self.stdout.write(
                self.style.SUCCESS(
                    "Secuencia de idRescate sincronizada correctamente en la base de datos."
                )
            )
