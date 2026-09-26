import logging
from textwrap import wrap

class SparseLogger:

    @staticmethod
    def get_logger():
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(levelname)s:%(name)s:%(message)s"
        )

        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
        return logger

    @staticmethod
    def generate_fn_logs(
    logger,
    model,
    query,
    response,
    msg,
    metadata="N/A"
):
        def format_box_text(text, width=56):
            if not text:
                return "║ <none>" + " " * 49 + "║"

            return "\n".join(
                f"║ {line:<56} ║"
                for line in wrap(str(text), width=56)
            )

        logger.debug(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║                       LLM RESPONSE                          ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"║ Model: {model:<52} ║\n"
            f"║ Finish reason: {response.choices[0].finish_reason!s:<43} ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ User Query                                                   ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{format_box_text(query)}\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ CONTENT                                                      ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{format_box_text(msg.content)}\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ TOOL CALLS                                                   ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{format_box_text(msg.tool_calls)}\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║ METADATA                                                     ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            f"{format_box_text(metadata)}\n"
            "╚══════════════════════════════════════════════════════════════╝"
        )


    @staticmethod
    def usual(logger , msg):
        logger.debug(msg)