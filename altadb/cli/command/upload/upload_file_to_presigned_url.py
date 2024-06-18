import aiohttp  # type: ignore
import aiofiles  # type: ignore
import asyncio


async def upload_file_to_presigned_url(
    file_paths: list[dict[str, str]],
    presigned_urls: list[str],
    semaphore: asyncio.Semaphore,
) -> bool:
    status = True
    async with semaphore:
        for file_path, presigned_url in zip(file_paths, presigned_urls):
            if len(presigned_url):
                async with aiofiles.open(
                    str(file_path.get("abs_file_path")), "rb"
                ) as file:
                    async with aiohttp.request(
                        "PUT",
                        presigned_url,
                        data=await file.read(),
                    ) as response:
                        if response.status == 200:
                            print(
                                f"Successfully uploaded file {file_path} to {presigned_url}"
                            )
                        else:
                            status = False
                            print(
                                f"Error uploading file {file_path} to {presigned_url}: {response.text}"
                            )
            else:
                print(f"No presigned URL found for {file_path}")
    return status


__all__ = [
    "upload_file_to_presigned_url",
]
