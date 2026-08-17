from cs336_data.language_identification import identify_language
from cs336_data.mask_pii import mask_emails, mask_phone_numbers
from cs336_data.reservoir_sample_gz import reservoir_sample_gz, save_samples
from cs336_data.multitheard_warc_scrapper import main


if __name__ == "__main__":
    # identify_language("This language is english what you say!")

    # text = """Contact us at support@example.com or sales.team+tech@company.co.uk.You can also reach out to john_doe123@domain.org."""
    # print(mask_phone_numbers(text))
    
    # print(mask_nsfw("The page contains explicit sexual content and pornography."))

    # text = """
    #     This is an adult-content website containing sexually explicit material intended only for adults. The page includes descriptions and discussions of pornography, nudity, sexual activity, erotic videos, adult performers, explicit scenes, and other sexually oriented media. The surrounding text repeatedly discusses adult entertainment, explicit photographs, sexual videos, erotic content, and pornography categories, with the primary purpose of directing readers toward sexually explicit material. 
    #     This content is not educational, medical, artistic, or incidental; sexual content is the central subject of the page.
    #     This is an adult-content website containing sexually explicit material intended only for adults. The page includes descriptions and discussions of pornography, nudity, sexual activity, erotic videos, adult performers, explicit scenes, and other sexually oriented media. The surrounding text repeatedly discusses adult entertainment, explicit photographs, sexual videos, erotic content, and pornography categories, with the primary purpose of directing readers toward sexually explicit material. 
    #     This content is not educational, medical, artistic, or incidental; sexual content is the central subject of the page.
    #     he article is an adult-oriented discussion of intimate relationships and sexual behavior between consenting adults. It contains references to nudity, sexual activity, and explicit adult material, but presents them within a longer discussion rather than as a simple list of explicit terms.
    #     he article is an adult-oriented discussion of intimate relationships and sexual behavior between consenting adults. It contains references to nudity, sexual activity, and explicit adult material, but presents them within a longer discussion rather than as a simple list of explicit terms.
    # """

    # text = """The discussion began as a technical review of the project, but one participant became increasingly hostile after their implementation was criticized. They repeatedly attacked another contributor personally instead of addressing the technical issues, calling them incompetent, useless, stupid, and a complete failure. They also mocked the contributor's ability to understand basic programming concepts and told other members that nobody should take their work seriously. Several replies continued the personal attacks, ridiculed the person for making mistakes, and encouraged others to exclude them from the project. The conversation eventually became dominated by insults, harassment, and hostile personal remarks rather than discussion of the original engineering problem. Even when another participant attempted to redirect the conversation toward the code and proposed a technical solution, the hostile participant continued attacking the individual and dismissing everything they said."""
    # text = "You are an idiot and nobody wants to hear your opinions. Your work is completely worthless.”"
    # text = "This is a terrible piece of work. You have no idea what you are doing, and this whole thing is garbage.”"
    # print(mask_toxic_speech(text))

    # gz_input_file = "data/enwiki-20260501-extracted_urls.txt.gz"
    # output_file = "data/subsampled_positive_urls.txt"
    # sample_size = 10_000

    # sampled_urls = reservoir_sample_gz(gz_input_file, k=sample_size, seed=42)
    # save_samples(sampled_urls, output_file)
    # print(f"Sampled {len(sampled_urls)} URLs and saved to {output_file}")

    main()
    