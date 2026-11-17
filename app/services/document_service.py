import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import pypdf
import docx
from app.config import UPLOAD_DIR
from app.services.translation_service import translation_service

logger = logging.getLogger("linguaflow.documents")

class DocumentService:
    def __init__(self):
        self.upload_dir = Path(UPLOAD_DIR)

    def extract_text_from_txt(self, file_path: Path) -> str:
        """Lee el contenido de un archivo de texto con manejo de codificaciones."""
        encodings = ["utf-8", "latin-1", "cp1252"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise ValueError("No se pudo decodificar el archivo de texto. Verifica la codificación.")

    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Extrae el texto de todas las páginas de un archivo PDF usando pypdf."""
        text_parts = []
        try:
            reader = pypdf.PdfReader(str(file_path))
            for i, page in enumerate(reader.pages):
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted.strip())
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extrayendo texto del PDF: {e}")
            raise ValueError(f"Error al procesar el archivo PDF: {e}")

    def extract_text_from_docx(self, file_path: Path) -> str:
        """Extrae el texto de párrafos y tablas de un archivo DOCX."""
        try:
            doc = docx.Document(str(file_path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        paragraphs.append(" | ".join(row_text))
            return "\n\n".join(paragraphs)
        except Exception as e:
            logger.error(f"Error leyendo DOCX: {e}")
            raise ValueError(f"Error al procesar el archivo Word DOCX: {e}")

    def extract_text(self, file_path: Path, filename: str) -> str:
        """Detecta la extensión y extrae el texto del documento."""
        ext = file_path.suffix.lower()
        if ext in [".txt", ".md", ".csv"]:
            return self.extract_text_from_txt(file_path)
        elif ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Formato no soportado: {ext}. Formatos permitidos: PDF, DOCX, TXT.")

    def create_translated_docx(self, original_title: str, translated_text: str, target_path: Path):
        """Crea un nuevo documento de Word formateado con la traducción."""
        doc = docx.Document()
        doc.add_heading(f"LinguaFlow - Traducción de: {original_title}", level=1)
        doc.add_paragraph("Traducción generada automáticamente por LinguaFlow.")
        doc.add_paragraph("-" * 50)

        for paragraph in translated_text.split("\n\n"):
            p = paragraph.strip()
            if p:
                doc.add_paragraph(p)
        doc.save(str(target_path))

    def create_translated_txt(self, translated_text: str, target_path: Path):
        """Crea un archivo de texto con la traducción en UTF-8."""
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(translated_text)

    async def process_document(
        self,
        file_bytes: bytes,
        original_filename: str,
        source_lang: str = "auto",
        target_lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Guarda temporalmente el archivo, extrae el texto, lo traduce por bloques
        y genera los archivos traducidos listos para descarga.
        """
        file_ext = Path(original_filename).suffix.lower()
        file_id = str(uuid.uuid4())[:8]
        safe_name = f"input_{file_id}{file_ext}"
        saved_input_path = self.upload_dir / safe_name

        # Guardar archivo recibido en disco
        with open(saved_input_path, "wb") as f:
            f.write(file_bytes)

        try:
            # 1. Extraer texto
            extracted_text = self.extract_text(saved_input_path, original_filename)
            if not extracted_text or not extracted_text.strip():
                raise ValueError("El documento no contiene texto legible.")

            # 2. Traducir texto manteniendo párrafos
            translation_result = await translation_service.translate_text(
                text=extracted_text,
                source_lang=source_lang,
                target_lang=target_lang
            )
            translated_text = translation_result["translated_text"]
            detected_lang = translation_result["detected_lang"]

            # 3. Generar archivo de salida según el tipo
            output_filename = f"LinguaFlow_{file_id}_{Path(original_filename).stem}_{target_lang}"
            
            if file_ext == ".docx":
                output_filename += ".docx"
                output_path = self.upload_dir / output_filename
                self.create_translated_docx(original_filename, translated_text, output_path)
            elif file_ext == ".pdf":
                # Para PDF generamos DOCX (fácilmente editable y compatible) y TXT
                output_filename += ".docx"
                output_path = self.upload_dir / output_filename
                self.create_translated_docx(original_filename, translated_text, output_path)
            else:
                output_filename += ".txt"
                output_path = self.upload_dir / output_filename
                self.create_translated_txt(translated_text, output_path)

            return {
                "file_id": file_id,
                "original_filename": original_filename,
                "output_filename": output_filename,
                "source_lang": source_lang,
                "detected_lang": detected_lang,
                "target_lang": target_lang,
                "original_character_count": len(extracted_text),
                "translated_character_count": len(translated_text),
                "extracted_preview": extracted_text[:500] + ("..." if len(extracted_text) > 500 else ""),
                "translated_preview": translated_text[:500] + ("..." if len(translated_text) > 500 else ""),
                "download_url": f"/api/documents/download/{output_filename}"
            }

        finally:
            # Limpiar archivo de entrada temporal
            if saved_input_path.exists():
                try:
                    os.remove(saved_input_path)
                except Exception as e:
                    logger.warning(f"No se pudo eliminar archivo temporal {saved_input_path}: {e}")

document_service = DocumentService()
