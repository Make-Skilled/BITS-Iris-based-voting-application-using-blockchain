// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract Voting {

    struct Voter {
        uint id;
        string fullName;
        string aadharNumber;
        string irisImagePath;
        string email;
        string password;
    }

    struct Party {
        uint pollId;
        string partyName;
        string partyLeader;
        string symbolPath;
        uint partyId;
    }

    struct Poll {
        uint pollId;
        string pollName;
        string pollDate;
        string startTime;
        string endTime;
    }

    uint private voterCounter = 0; // Auto-incrementing voter ID
    mapping(string => Voter) public voters;
    string[] public voterAadhars;

    mapping(uint => Party) private parties;
    Party[] public allParties;

    uint private pollCounter = 0;
    mapping(uint => Poll) public polls;
    uint[] private pollIds;

    // Struct for storing votes for each poll
    struct Vote {
        uint pollId;
        mapping(uint => uint) partyVotes; // Maps partyId to vote count
        uint[] partyIds; // List of all partyIds in the poll
        bool initialized; // Flag to track if poll exists
    }

    // Struct for tracking who has voted in each poll
    struct PolledIds {
        uint pollId;
        mapping(string => bool) hasVoted; // Maps Aadhaar number to voting status
    }

    // Mappings for votes and voter tracking
    mapping(uint => Vote) public pollVotes; // Maps pollId to Vote struct
    mapping(uint => PolledIds) public polledVoters; // Maps pollId to PolledIds struct

    function registerVoter(
        string memory _fullName,
        string memory _aadharNumber,
        string memory _irisImagePath,
        string memory _email,
        string memory _password
    ) public {
        require(bytes(voters[_aadharNumber].aadharNumber).length == 0, "Voter already registered with this Aadhar number");

        voterCounter++; // Auto-increment voter ID

        voters[_aadharNumber] = Voter({
            id: voterCounter,
            fullName: _fullName,
            aadharNumber: _aadharNumber,
            irisImagePath: _irisImagePath,
            email: _email,
            password: _password
        });

        voterAadhars.push(_aadharNumber);
    }

    function getPollById(uint _pollId) public view returns (uint, string memory, string memory, string memory, string memory) {
        require(bytes(polls[_pollId].pollName).length > 0, "Poll does not exist");

        Poll memory poll = polls[_pollId];
        return (poll.pollId, poll.pollName, poll.pollDate, poll.startTime, poll.endTime);
    }

    function getPartiesByPartyId(uint partyId) public view returns (Party[] memory) {
        uint count = 0;

        for (uint i = 0; i < allParties.length; i++) {
            if (allParties[i].pollId == partyId) {
                count++;
            }
        }

        Party[] memory result = new Party[](count);
        uint index = 0;

        for (uint i = 0; i < allParties.length; i++) {
            if (allParties[i].pollId == partyId) {
                result[index] = allParties[i];
                index++;
            }
        }

        return result;
    }

    function getVoter(string memory aadhar) public view returns (uint, string memory, string memory, string memory, string memory, string memory) {
        require(bytes(voters[aadhar].aadharNumber).length > 0, "Voter not registered");

        Voter memory voter = voters[aadhar];
        return (voter.id, voter.fullName, voter.aadharNumber, voter.irisImagePath, voter.email, voter.password);
    }

    function getAllVoters() public view returns (Voter[] memory) {
        Voter[] memory allVoters = new Voter[](voterAadhars.length);
        for (uint i = 0; i < voterAadhars.length; i++) {
            allVoters[i] = voters[voterAadhars[i]];
        }
        return allVoters;
    }
    uint partyCounter;
    function addParty(uint _id, string memory _partyName, string memory _partyLeader, string memory _symbolPath) public {
        partyCounter++;
        parties[_id] = Party(_id, _partyName, _partyLeader, _symbolPath,partyCounter);
        allParties.push(Party(_id, _partyName, _partyLeader, _symbolPath,partyCounter));
    }

    function getParty(uint _id) public view returns (uint, string memory, string memory, string memory) {
        require(bytes(parties[_id].partyName).length > 0, "Party does not exist");

        Party memory party = parties[_id];
        return (party.pollId, party.partyName, party.partyLeader, party.symbolPath);
    }

    function addPoll(string memory _pollName, string memory _pollDate, string memory _startTime, string memory _endTime) public {
        pollCounter++;

        polls[pollCounter] = Poll(pollCounter, _pollName, _pollDate, _startTime, _endTime);
        pollIds.push(pollCounter);
    }

    function getAllPolls() public view returns (Poll[] memory) {
        Poll[] memory allPolls = new Poll[](pollIds.length);
        for (uint i = 0; i < pollIds.length; i++) {
            allPolls[i] = polls[pollIds[i]];
        }
        return allPolls;
    }

    function vote(uint _pollId, uint _partyId, string memory _aadharNumber) public {
        require(bytes(voters[_aadharNumber].aadharNumber).length > 0, "Voter not registered");
        require(!polledVoters[_pollId].hasVoted[_aadharNumber], "Already voted!");
        require(bytes(polls[_pollId].pollName).length > 0, "Poll does not exist");

        // Initialize poll if first vote
        if (!pollVotes[_pollId].initialized) {
            pollVotes[_pollId].initialized = true;
            pollVotes[_pollId].pollId = _pollId;
        }

        // Record vote
        if (pollVotes[_pollId].partyVotes[_partyId] == 0) {
            pollVotes[_pollId].partyIds.push(_partyId);
        }
        pollVotes[_pollId].partyVotes[_partyId]++;

        // Mark Aadhaar as voted
        polledVoters[_pollId].hasVoted[_aadharNumber] = true;
    }

    function getVotes(uint _pollId, uint _partyId) public view returns (uint) {
        require(pollVotes[_pollId].initialized, "Poll has no votes");
        return pollVotes[_pollId].partyVotes[_partyId];
    }

    function hasVoted(uint _pollId, string memory _aadharNumber) public view returns (bool) {
        return polledVoters[_pollId].hasVoted[_aadharNumber];
    }

    function getPollResults(uint _pollId) public view returns (uint[] memory partyIds, uint[] memory voteCounts) {
        require(pollVotes[_pollId].initialized, "Poll does not exist!");

        uint totalParties = pollVotes[_pollId].partyIds.length;
        partyIds = new uint[](totalParties);
        voteCounts = new uint[](totalParties);

        for (uint i = 0; i < totalParties; i++) {
            uint partyId = pollVotes[_pollId].partyIds[i];
            partyIds[i] = partyId;
            voteCounts[i] = pollVotes[_pollId].partyVotes[partyId];
        }

        return (partyIds, voteCounts);
    }

    function deleteVoter(string memory _aadharNumber) public {
        require(bytes(voters[_aadharNumber].aadharNumber).length > 0, "Voter not found");
        
        // Remove from mapping
        delete voters[_aadharNumber];
        
        // Remove from array
        for (uint i = 0; i < voterAadhars.length; i++) {
            if (keccak256(bytes(voterAadhars[i])) == keccak256(bytes(_aadharNumber))) {
                // Move the last element to the position of the element to delete
                voterAadhars[i] = voterAadhars[voterAadhars.length - 1];
                // Remove the last element
                voterAadhars.pop();
                break;
            }
        }
    }

}
