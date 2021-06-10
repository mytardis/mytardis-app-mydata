import os
import math
import logging

from django.conf import settings

from tardis.celery import tardis_app
from tardis.tardis_portal import tasks

from tardis.tardis_portal.models.datafile import DataFileObject
from .models.chunk import Chunk


logger = logging.getLogger(__name__)


@tardis_app.task(name="tardis_portal.complete_chunked_upload", ignore_result=True)
def complete_chunked_upload(dfo_id):
    """
    Assembly data file from chunks
    """
    def make_file(dfo, chunk_ids, data_path, chunk_size):
        """
        Reassembly file from chunks
        """
        for chunk_id in chunk_ids:
            file_path = os.path.join(data_path, chunk_id)
            if not os.path.exists(file_path):
                raise Exception("Missing chunk file %s" % file_path)

        dst_path = dfo.get_full_path()
        dst_dir = os.path.dirname(dst_path)

        # Make new folder
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        # If destination file already exists,
        # open file and seek to the last offset
        if os.path.exists(dst_path):
            file_size = os.stat(dst_path).st_size
            chunks_offset = max(math.ceil(file_size/chunk_size) - 1, 0)
            dst = open(dst_path, "w+b")
            dst.seek(chunks_offset * chunk_size)
        else:
            # Make new file
            chunks_offset = 0
            dst = open(dst_path, "wb")

        for chunk_id in chunk_ids[chunks_offset:]:
            file_path = os.path.join(data_path, chunk_id)
            logger.info("Complete file %s chunk %s" % (dfo.id, chunk_id))
            with open(file_path, "rb") as src:
                while True:
                    data = src.read(settings.CHUNK_COPY_SIZE)
                    dst.write(data)
                    if len(data) != settings.CHUNK_COPY_SIZE:
                        src.close()
                        break

        # Close the file
        dst.close()

    logger.info("Complete file %s" % dfo_id)
    dfo = DataFileObject.objects.get(id=dfo_id)
    chunks = Chunk.objects.filter(dfo_id=dfo.id).order_by("offset")
    chunk_ids = [chunk.chunk_id for chunk in chunks]
    logger.debug("Complete file %s total chunks %s " % (dfo_id, len(chunk_ids)))
    if len(chunk_ids) != 0:
        data_path = os.path.join(settings.CHUNK_STORAGE, str(dfo.id))
        # Copy chunks to a final destination
        try:
            logger.debug("Complete file %s assembly" % dfo_id)
            make_file(dfo, chunk_ids, data_path, chunks[0].size)
            logger.debug("Complete file %s file ready" % dfo.id)
        except Exception as e:
            logger.error("Complete file %s error %s" % (dfo_id, str(e)))
            return False
        # Cleanup
        logger.debug("Complete file %s cleanup" % dfo_id)
        chunks.delete()
        for chunk_id in chunk_ids:
            try:
                os.remove(os.path.join(data_path, chunk_id))
            except Exception as e:
                logger.error(str(e))
        # Folder must be empty
        try:
            os.rmdir(data_path)
        except Exception as e:
            logger.error(str(e))

    # Verify file
    logger.debug("Complete file %s verify" % dfo_id)
    tasks.dfo_verify.apply_async(
        args=[dfo.id],
        priority=dfo.priority)

    return True


@tardis_app.task(name="tardis_portal.remove_chunked_upload", ignore_result=True)
def remove_chunked_upload(dfo_id):
    logger.debug("Remove incomplete upload %s" % dfo_id)
    chunks = Chunk.objects.filter(dfo_id=dfo_id).order_by("offset")
    chunk_ids = [chunk.chunk_id for chunk in chunks]
    if len(chunk_ids) != 0:
        data_path = os.path.join(settings.CHUNK_STORAGE, str(dfo_id))
        for chunk_id in chunk_ids:
            try:
                os.remove(os.path.join(data_path, chunk_id))
            except Exception as e:
                logger.error(str(e))
        try:
            os.rmdir(data_path)
        except Exception as e:
            logger.error(str(e))
        chunks.delete()


@tardis_app.task(name="tardis_portal.chunks_cleanup", ignore_result=True)
def chunks_cleanup():
    """
    Find lost chunks (due to incomplete uploads) and cleanup
    """
    uploads = Chunk.objects.order_by("dfo_id").values("dfo_id").distinct()
    for upload in uploads:
        dfo = DataFileObject.objects.filter(id=upload["dfo_id"])
        if len(dfo) == 0:
            remove_chunked_upload.apply_async(dfo[0].id)


@tardis_app.task(name="tardis_portal.chunks_complete", ignore_result=True)
def chunks_complete():
    """
    Find and try to complete uploads not processed straight after upload
    """
    uploads = Chunk.objects.order_by("dfo_id").values("dfo_id").distinct()
    for upload in uploads:
        dfo = DataFileObject.objects.filter(id=upload["dfo_id"])
        if len(dfo) != 0:
            last_chunk = Chunk.objects.filter(
                dfo_id=dfo[0].id
            ).order_by("-offset")[0]
            offset = min(
                last_chunk.offset+last_chunk.size,
                dfo[0].datafile.size)
            if offset == dfo[0].datafile.size:
                complete_chunked_upload.apply_async(args=[dfo[0].id])
