class FormData(BaseModel):
    prompt: str  # fun fact , history video
    duration: str  # frontend : take int
    aspect_ratio: str
    style: str
    voice_character: str = ""
    bgm_audio: Optionalstr = ""  # add bgm option (optional)
    voice_files: List[UploadFile] = File(None)


@app.post("/generate-video")
## ORIGINAL
# async def handle_video_request(data: Annotated[FormData, Form()]):

## t1
# async def handle_video_request(
#     prompt: str = Form(...),
#     duration: int = Form(...),
#     aspect_ratio: str = Form(...),
#     style: str = Form(...),
#     voice_character: Optional[str] = Form(""),
#     bgm_audio: Optional[str] = Form(""),
#     voice_files: Optional[List[UploadFile]] = File(None),
# ):

## t2
async def handle_video_request(
    prompt: str = Form(...),
    duration: int = Form(...),
    aspect_ratio: str = Form(...),
    style: str = Form(...),
    voice_character: Optional[str] = Form(""),
    bgm_audio: Optional[str] = Form(""),
    voice_files: Optional[List[UploadFile]] = None,  # Remove File() dependency
):
    print(prompt)
    print(duration)
    print(aspect_ratio)
    print(bgm_audio)
    print(style)
    print(voice_character)
    print(voice_files)

    # Parameter validation
    if int(duration) not in VALID_DURATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid duration. Allowed values are {VALID_DURATIONS}.",
        )

    # set img aspect ratio
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise HTTPException(
            status_code=400, detail=f"Invalid aspect ratio: {aspect_ratio}"
        )
    # aspect_ratio = data.aspect_ratio

    if style not in VALID_STYLES:
        raise HTTPException(
            status_code=400, detail=f"Invalid style. Allowed styles are {VALID_STYLES}."
        )

    if voice_character not in DEFAULT_VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid voice. Allowed voices are {DEFAULT_VOICES.keys()}.",
        )
    # # TODO: check bgm voices

    uploaded_files = []
    try:
        # Handle voice files if provided
        if voice_files:
            # Create uploads directory
            uploads_dir = Path("uploads")
            uploads_dir.mkdir(exist_ok=True)

            # Save all uploaded files
            uploaded_files = []
            for i, voice_file in enumerate(voice_files, start=1):
                file_path = str(uploads_dir / f"sample_{i}.mp3")
                with open(file_path, "wb") as f:
                    f.write(await voice_file.read())
                uploaded_files.append(file_path)

                # Check audio duration
                audio_duration = get_audio_duration(file_path)
                if audio_duration > MAX_VOICE_FILE_DURATION:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Each voice file must be under {MAX_VOICE_FILE_DURATION} seconds.",
                    )

        # Generate video
        await generate_video(
            prompt=prompt,
            duration=int(duration),
            style=style,
            aspect_ratio=aspect_ratio,  # video aspect ratio
            bgm_audio=bgm_audio,
            voice_character=voice_character,
            voice_files=uploaded_files if uploaded_files else None,
        )

        # # upload video to s3
        # if bgm_audio != "":
        #     video_path = "video_creation/assets/videos/final_output_video_bgm.mp4"
        # else:
        #     video_path = "video_creation/assets/videos/final_output_video_subtitles.mp4"
        # s3_url = upload_to_s3(file_path=video_path, duration=duration)
        # logger.info(f"S3 URL: {s3_url}")

        # # delete all videos after s3 upload
        # clean_video_folder()

        return JSONResponse({"success": True, "video_path": "s3_url"})  # aws s3 link

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")

        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )
    finally:
        # Clean up uploaded files
        for file_path in uploaded_files:
            try:
                Path(file_path).unlink()
            except Exception as e:
                logger.error(f"Error deleting uploaded file {file_path}: {str(e)}")
