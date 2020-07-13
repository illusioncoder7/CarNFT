from iconservice import *

TAG = "CarToken"


class TokenStandard(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def symbol(self) -> str:
        pass

    @abstractmethod
    def balanceOf(self, _owner: Address) -> int:
        pass

    @abstractmethod
    def ownerOf(self, _tokenId: int) -> Address:
        pass

    @abstractmethod
    def getApproved(self, _tokenId: int) -> Address:
        pass

    @abstractmethod
    def approve(self, _to: Address, _tokenId: int):
        pass

    @abstractmethod
    def transfer(self, _to: Address, _tokenId: int):
        pass

    @abstractmethod
    def transferFrom(self, _from: Address, _to: Address, _tokenId: int):
        pass


class CarToken(IconScoreBase, TokenStandard):
    _CAR_OWNER = "car_owner"  # to find the owner of the car token against the tokenId
    _OWNER_CAR_COUNT = "owner_car_count"  # to find the total count of car tokens of an user
    _CAR_ID_LIST = "car_id_list"  # to list the tokenId of all the car tokens
    _CARS = "cars"  # for  the token properties of all car tokens against their ids
    _CAR_APPROVALS = "car_approvals"  # to track the car tokens approved by the owners for transfers
    _ZERO_ADDRESS = Address.from_prefix_and_int(AddressPrefix.EOA, 0)

    @eventlog(indexed=3)
    def Approval(self, _owner: Address, _approved: Address, _tokenId: int):
        pass

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _tokenId: int):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._car_owner = DictDB("_CAR_OWNER", db, value_type=Address)
        self._owner_car_count = DictDB("_OWNER_CAR_COUNT", db, value_type=int)
        self._car_id_list = ArrayDB("_CAR_ID_LIST", db, value_type=str)
        self._cars = DictDB("_CARS", db, value_type=str, depth=2)
        self._car_approvals = DictDB("_CAR_APPROVALS", db, value_type=Address)

    def on_install(self, initialSupply: int, decimals: int) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        """
        Returns the name of the token.Any name can be given to token
        """
        return "CarToken"

    @external(readonly=True)
    def symbol(self) -> str:
        """
        Returns the symbol of the token.
        """
        return "CAR"

    @external(readonly=True)
    def balanceOf(self, _owner: Address) -> int:
        """
        Returns the number of NFTs owned by _owner.
        NFTs assigned to the zero address are considered invalid,
        so this function SHOULD throw for queries about the zero address.
        """
        if _owner is None or self._is_zero_address(_owner):
            revert("Invalid owner")
        return self._owner_car_count[_owner]

    @external(readonly=True)
    def ownerOf(self, _carId: int) -> Address:
        """
        Returns the owner of an NFT. Throws if _tokenId is not a valid NFT.
        """
        self._id_validity(str(_carId))
        owner = self._car_owner[str(_carId)]
        if self._is_zero_address(owner):
            revert("Invalid car Id. Car is burned")
        return owner

    @external(readonly=True)
    def getApproved(self, _carId: int) -> Address:
        """
        Returns the approved address for a single NFT.
        If there is none, returns the zero address.
        Throws if _tokenId is not a valid NFT.
        """
        owner = self.ownerOf(_carId)
        if owner is None:
            revert("Invalid token id ")
        addr = self._car_approvals[str(_carId)]
        if addr is None:
            return self._ZERO_ADDRESS
        return addr

    @external
    def approve(self, _to: Address, _carId: int):
        """
        Allows _to to change the ownership of _tokenId from your account. 
        The zero address indicates there is no approved address. 
        Throws unless self.msg.sender is the current NFT owner.
        """
        owner = self.ownerOf(_carId)
        if _to == owner:
            revert("Can't approve to yourself.")
        if self.msg.sender != owner:
            revert("You do not own this NFT")

        self._car_approvals[str(_carId)] = _to
        self.Approval(owner, _to, _carId)

    @external
    def transfer(self, _to: Address, _carId: int):
        """
        Transfers the ownership of your NFT to another address, 
        and MUST fire the Transfer event. Throws unless self.msg.sender 
        is the current owner. Throws if _to is the zero address. 
        Throws if _tokenId is not a valid NFT.
        """
        if self.ownerOf(_carId) is None:
            revert("The car Id is invalid")
        if self._is_zero_address(_to):
            revert("Cant transfer to zero address")
        if self.ownerOf(_carId) != self.msg.sender:
            revert("You don't have permission to transfer this NFT")
        approved = self.getApproved(_carId)
        if approved != _to:
            revert("The transfer of car is not approved to given address")
        self._transfer(self.msg.sender, _to, _carId)

    @external
    def transferFrom(self, _from: Address, _to: Address, _carId: int):
        """
        Transfers the ownership of an NFT from one address to another address, 
        and MUST fire the Transfer event. Throws unless self.msg.sender is the 
        current owner or the approved address for the NFT. Throws if _from is 
        not the current owner. Throws if _to is the zero address. Throws if 
        _tokenId is not a valid NFT.
        """
        if self.ownerOf(_carId) != self.msg.sender and self._car_approvals[str(_carId)] != self.msg.sender:
            revert("You are not authorized to transfer the car")
        if self.ownerOf(_carId) != _from:
            revert("Invalid address of the Car owner")
        if self._is_zero_address(_to):
            revert("Invalid address of the receiver")
        approved = self.getApproved(_carId)
        if approved != _to:
            revert("The transfer of car is not approved to given address")
        self._transfer(_from, _to, _carId)

    @external
    def create_car(self, _company_name: str, _model: str, _engine_power: str, _price: str, _fuel_type: str):
        car_features = {"company": _company_name, "model": _model, "engine_power": _engine_power, "price": _price,
                        "fuel_type": _fuel_type}
        carId = str(self.current_supply() + 1)
        self._car_id_list.put(carId)
        self._owner_car_count[self.msg.sender] += 1
        self._car_owner[carId] = self.msg.sender
        self._cars[carId]["features"] = json_dumps(car_features)

    def _id_validity(self, _carId: int):
        if str(_carId) not in self._car_id_list:
            revert("No car with given Id found")

    @external(readonly=True)
    def current_supply(self) -> int:
        return len(self._car_id_list)

    @external(readonly=True)
    def get_car(self, _carId: int) -> dict:
        self._id_validity(_carId)
        car_features = json_loads(self._cars[str(_carId)]["features"])
        car_features["owner"] = self.ownerOf(_carId)
        return car_features

    def _is_zero_address(self, _address: Address) -> bool:
        # Check if address is zero address
        if _address == self._ZERO_ADDRESS:
            return True
        return False

    def _transfer(self, _from: Address, _to: Address, _carId: int):
        del self._car_approvals[str(_carId)]
        self._car_owner[str(_carId)] = _to
        self._owner_car_count[_to] += 1
        self._owner_car_count[_from] -= 1
        self.Transfer(_from, _to, _carId)
