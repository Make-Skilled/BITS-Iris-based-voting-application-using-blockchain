// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract Voting {

    struct Voter {
        string fullName;
        string aadharNumber;
        string irisImagePath;
        string email;
        string password;
    }

    struct Party {
        uint id;
        string partyName;
        string partyLeader;
        string symbolPath;
    }

    struct Poll {
        uint pollId;
        string pollName;
        string pollDate;
        string startTime;
        string endTime;
    }

    mapping(string => Voter) public voters;
    string[] public voterAadhars;

    mapping(uint => Party) private parties; // Store parties by ID
    Party[] public allParties;

    uint private pollCounter = 0;  // Auto-incrementing poll ID
    mapping(uint => Poll) public polls;
    uint[] private pollIds;  // To track all poll IDs

    function registerVoter(
        string memory _fullName,
        string memory _aadharNumber,
        string memory _irisImagePath,
        string memory _email,
        string memory _password
    ) public {
        require(bytes(voters[_aadharNumber].aadharNumber).length == 0, "Voter already registered with this Aadhar number");

        voters[_aadharNumber] = Voter({
            fullName: _fullName,
            aadharNumber: _aadharNumber,
            irisImagePath: _irisImagePath,
            email: _email,
            password: _password
        });

        voterAadhars.push(_aadharNumber);
    }

    function getVoter(string memory aadhar) public view returns (string memory, string memory, string memory, string memory, string memory) {
        require(bytes(voters[aadhar].aadharNumber).length > 0, "Voter not registered");

        Voter memory voter = voters[aadhar];
        return (voter.fullName, voter.aadharNumber, voter.irisImagePath, voter.email, voter.password);
    }

    // Function to add a new party (now accepts `id` as an argument)
    function addParty(uint _id, string memory _partyName, string memory _partyLeader, string memory _symbolPath) public {

        parties[_id] = Party(_id, _partyName, _partyLeader, _symbolPath);
        allParties.push(Party(_id, _partyName, _partyLeader, _symbolPath));
    }

    // Function to get a party by ID
    function getParty(uint _id) public view returns (uint, string memory, string memory, string memory) {
        require(bytes(parties[_id].partyName).length > 0, "Party does not exist");

        Party memory party = parties[_id];
        return (party.id, party.partyName, party.partyLeader, party.symbolPath);
    }

    // Function to get all parties with a specific ID
function getPartiesByPartyId(uint partyId) public view returns (Party[] memory) {
    uint count = 0;

    // Count how many parties have the given ID
    for (uint i = 0; i < allParties.length; i++) {
        if (allParties[i].id == partyId) {
            count++;
        }
    }

    // Create a dynamic array to store matching parties
    Party[] memory result = new Party[](count);
    uint index = 0;

    // Add matching parties to the result array
    for (uint i = 0; i < allParties.length; i++) {
        if (allParties[i].id == partyId) {
            result[index] = allParties[i];
            index++;
        }
    }

    return result;
}

function addPoll(string memory _pollName, string memory _pollDate, string memory _startTime, string memory _endTime) public {
        pollCounter++;  // Auto-increment ID

        polls[pollCounter] = Poll(pollCounter, _pollName, _pollDate, _startTime, _endTime);
        pollIds.push(pollCounter);  // Store poll ID
    }

        function getAllPolls() public view returns (Poll[] memory) {
        Poll[] memory allPolls = new Poll[](pollIds.length);
        for (uint i = 0; i < pollIds.length; i++) {
            allPolls[i] = polls[pollIds[i]];
        }
        return allPolls;
    }

        // Function to get poll details by pollId
    function getPollById(uint _pollId) public view returns (uint, string memory, string memory, string memory, string memory) {
        require(bytes(polls[_pollId].pollName).length > 0, "Poll does not exist");

        Poll memory poll = polls[_pollId];
        return (poll.pollId, poll.pollName, poll.pollDate, poll.startTime, poll.endTime);
    }

}
