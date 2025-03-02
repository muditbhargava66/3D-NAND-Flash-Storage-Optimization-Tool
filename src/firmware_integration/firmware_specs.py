# src/firmware_integration/firmware_specs.py

import logging

import yaml
from jsonschema import ValidationError, validate


class FirmwareSpecGenerator:
    def __init__(self, template_file=None, config=None):
        self.template_file = template_file or "resources/config/template.yaml"
        self.output_file = "firmware_spec.yaml"
        self.config = config

    def generate_spec(self, config=None):
        """
        Generates a firmware specification based on the provided configuration.

        Args:
            config: Dictionary containing configuration parameters. If None, uses self.config.

        Returns:
            str: The generated firmware specification as a YAML string
        """
        try:
            if self.template_file:
                with open(self.template_file, "r") as file:
                    template = yaml.safe_load(file)
            else:
                template = {}
        except FileNotFoundError:
            # If template file doesn't exist, start with an empty template
            template = {}

        spec = template.copy()

        # If config is provided, use it directly
        config_to_use = config or self.config or {}

        spec["firmware_version"] = config_to_use.get("firmware_version", "N/A")
        spec["nand_config"] = config_to_use.get("nand_config", {})
        spec["ecc_config"] = config_to_use.get("ecc_config", {})
        spec["bbm_config"] = config_to_use.get("bbm_config", {})
        spec["wl_config"] = config_to_use.get("wl_config", {})

        # Convert the spec dictionary to a YAML string
        spec_str = yaml.dump(spec, default_flow_style=False)
        return spec_str

    def save_spec(self, spec, output_file=None):
        """
        Saves the generated specification to a file.

        Args:
            spec (str): The specification string to save
            output_file (str, optional): The file path to save to. Defaults to self.output_file.
        """
        output_path = output_file or self.output_file
        with open(output_path, "w") as file:
            file.write(spec)


class FirmwareSpecValidator:
    """
    Validates firmware specifications against defined schema and rules.

    This class ensures that firmware specifications meet all requirements
    for compatibility and correctness before deployment to NAND devices.
    """

    # Define firmware specification schema
    SCHEMA = {
        "type": "object",
        "required": ["firmware_version", "nand_config"],
        "properties": {
            "firmware_version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},  # Semantic versioning pattern
            "nand_config": {
                "type": "object",
                "required": ["page_size", "block_size", "num_blocks"],
                "properties": {
                    "page_size": {"type": "integer", "minimum": 512, "maximum": 32768},
                    "block_size": {"type": "integer", "minimum": 16384},
                    "num_blocks": {"type": "integer", "minimum": 1},
                    "num_planes": {"type": "integer", "minimum": 1},
                    "oob_size": {"type": "integer", "minimum": 0},
                },
            },
            "ecc_config": {
                "type": "object",
                "properties": {
                    "algorithm": {"type": "string", "enum": ["bch", "ldpc", "rs", "none"]},
                    "bch_params": {
                        "type": "object",
                        "properties": {
                            "m": {"type": "integer", "minimum": 3, "maximum": 16},
                            "t": {"type": "integer", "minimum": 1},
                        },
                    },
                    "ldpc_params": {
                        "type": "object",
                        "properties": {
                            "n": {"type": "integer", "minimum": 16},
                            "d_v": {"type": "integer", "minimum": 2},
                            "d_c": {"type": "integer", "minimum": 2},
                        },
                    },
                },
            },
            "bbm_config": {
                "type": "object",
                "properties": {
                    "max_bad_blocks": {"type": "integer", "minimum": 0},
                    "bad_block_ratio": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                },
            },
            "wl_config": {
                "type": "object",
                "properties": {
                    "wear_level_threshold": {"type": "integer", "minimum": 1},
                    "wear_leveling_method": {"type": "string", "enum": ["static", "dynamic", "hybrid"]},
                },
            },
        },
    }

    def __init__(self, logger=None):
        """
        Initialize the validator.

        Args:
            logger: Optional logger instance to use for logging validation issues
        """
        self.logger = logger or logging.getLogger(__name__)
        self.validation_errors = []

    def validate(self, firmware_spec):
        """
        Validate the firmware specification against schema and rules.

        Args:
            firmware_spec: Dictionary or YAML string of the firmware specification

        Returns:
            bool: True if specification is valid, False otherwise

        Note:
            Detailed errors are stored in self.validation_errors
        """
        self.validation_errors = []

        # Convert string to dictionary if needed
        if isinstance(firmware_spec, str):
            try:
                firmware_spec = yaml.safe_load(firmware_spec)
            except yaml.YAMLError as e:
                self.validation_errors.append(f"Invalid YAML format: {str(e)}")
                return False

        # Schema validation
        try:
            validate(instance=firmware_spec, schema=self.SCHEMA)
        except ValidationError as e:
            self.validation_errors.append(f"Schema validation failed: {str(e)}")
            self.logger.error(f"Schema validation failed: {str(e)}")
            return False

        # Additional custom validations
        if not self._validate_block_size_alignment(firmware_spec):
            return False

        if not self._validate_ecc_configuration(firmware_spec):
            return False

        if not self._validate_wear_leveling_config(firmware_spec):
            return False

        # All validations passed
        return True

    def get_errors(self):
        """
        Get all validation errors.

        Returns:
            list: List of validation error messages
        """
        return self.validation_errors

    def _validate_block_size_alignment(self, spec):
        """
        Validate that block size is a multiple of page size.

        Args:
            spec: Firmware specification dictionary

        Returns:
            bool: True if valid, False otherwise
        """
        nand_config = spec.get("nand_config", {})
        page_size = nand_config.get("page_size")
        block_size = nand_config.get("block_size")

        if page_size and block_size:
            if block_size % page_size != 0:
                error = f"Block size ({block_size}) must be a multiple of page size ({page_size})"
                self.validation_errors.append(error)
                self.logger.error(error)
                return False

        return True

    def _validate_ecc_configuration(self, spec):
        """
        Validate ECC configuration details.

        Args:
            spec: Firmware specification dictionary

        Returns:
            bool: True if valid, False otherwise
        """
        ecc_config = spec.get("ecc_config", {})
        if not ecc_config:
            return True  # No ECC config to validate

        algorithm = ecc_config.get("algorithm")

        if algorithm == "bch":
            bch_params = ecc_config.get("bch_params", {})
            m = bch_params.get("m")
            t = bch_params.get("t")

            if m and t and t > 2 ** (m - 1) - 1:
                error = f"BCH parameter t ({t}) exceeds maximum correctable errors for m={m}"
                self.validation_errors.append(error)
                self.logger.error(error)
                return False

        elif algorithm == "ldpc":
            ldpc_params = ecc_config.get("ldpc_params", {})
            n = ldpc_params.get("n")
            d_v = ldpc_params.get("d_v")
            d_c = ldpc_params.get("d_c")

            # Check if d_v and d_c are compatible with n
            if n and d_v and d_c:
                if (n * d_v) % d_c != 0:
                    error = f"LDPC parameters are incompatible: n={n}, d_v={d_v}, d_c={d_c}"
                    self.validation_errors.append(error)
                    self.logger.error(error)
                    return False

        return True

    def _validate_wear_leveling_config(self, spec):
        """
        Validate wear leveling configuration.

        Args:
            spec: Firmware specification dictionary

        Returns:
            bool: True if valid, False otherwise
        """
        wl_config = spec.get("wl_config", {})
        if not wl_config:
            return True  # No wear leveling config to validate

        threshold = wl_config.get("wear_level_threshold")
        nand_config = spec.get("nand_config", {})
        num_blocks = nand_config.get("num_blocks")

        # Check that threshold isn't too large compared to number of blocks
        if threshold and num_blocks and threshold > num_blocks * 100:
            error = f"Wear level threshold ({threshold}) is too high for the number of blocks ({num_blocks})"
            self.validation_errors.append(error)
            self.logger.error(error)
            return False

        return True
